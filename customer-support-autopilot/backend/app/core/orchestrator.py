"""
Core orchestrator for customer support conversations.

Uses LangGraph to orchestrate the flow: classify → retrieve → execute_tool → respond.
"""
import logging
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

from app.config import get_settings
from app.core.classifier import classify_intent
from app.core.rag_engine import retrieve_knowledge
from app.tools.shopify import get_order_info
from app.tools.stripe import process_refund
from app.core.fallback import escalate_to_human

logger = logging.getLogger(__name__)
settings = get_settings()


# Define the state schema
class ConversationState(dict):
    """State schema for the conversation graph."""
    pass


# Define tools
@tool
def lookup_order(order_id: str) -> Dict[str, Any]:
    """Look up order information by order ID."""
    return get_order_info(order_id)


@tool
def issue_refund(payment_intent_id: str, amount: int, reason: str = "") -> Dict[str, Any]:
    """Issue a refund for a payment."""
    return process_refund(payment_intent_id, amount, reason)


async def classify_node(state: ConversationState) -> ConversationState:
    """Classify the user's intent."""
    message = state.get("message", "")
    conversation_history = state.get("conversation_history", [])
    
    intent_result = await classify_intent(message, conversation_history)
    state["intent"] = intent_result["intent"]
    state["confidence"] = intent_result.get("confidence", 0.0)
    state["sentiment"] = intent_result.get("sentiment", "neutral")
    
    logger.info(f"Classified intent: {state['intent']} (confidence: {state['confidence']})")
    
    return state


async def retrieve_node(state: ConversationState) -> ConversationState:
    """Retrieve relevant knowledge base articles."""
    message = state.get("message", "")
    
    # Retrieve from RAG
    chunks = await retrieve_knowledge(message, top_k=3)
    state["retrieved_chunks"] = chunks
    
    logger.info(f"Retrieved {len(chunks)} knowledge chunks")
    
    return state


async def execute_tool_node(state: ConversationState) -> ConversationState:
    """Execute appropriate tool based on intent."""
    intent = state.get("intent", "")
    message = state.get("message", "")
    
    tool_result = None
    
    if intent == "order_status":
        # Try to extract order ID from message
        # In production, use LLM to extract structured data
        tool_result = {"status": "Order lookup requires order ID"}
        
    elif intent == "refund_request":
        # Check if we have enough information
        tool_result = {"status": "Refund request received, processing..."}
        
    state["tool_result"] = tool_result
    
    return state


async def respond_node(state: ConversationState) -> ConversationState:
    """Generate final response using Groq LLM."""
    from app.integrations.groq_client import generate_response
    
    message = state.get("message", "")
    intent = state.get("intent", "")
    retrieved_chunks = state.get("retrieved_chunks", [])
    tool_result = state.get("tool_result")
    conversation_history = state.get("conversation_history", [])
    
    # Generate response
    response_result = await generate_response(
        message=message,
        intent=intent,
        context=retrieved_chunks,
        tool_result=tool_result,
        conversation_history=conversation_history,
    )
    
    state["response"] = response_result["response"]
    state["tokens_used"] = response_result.get("tokens_used", 0)
    
    return state


async def check_escalation(state: ConversationState) -> str:
    """Check if escalation to human is needed."""
    intent = state.get("intent", "")
    confidence = state.get("confidence", 0.0)
    sentiment = state.get("sentiment", "neutral")
    
    # Escalate if:
    # - Intent is human_escalation
    # - Low confidence
    # - Negative sentiment
    if intent == "human_escalation" or confidence < 0.5 or sentiment == "negative":
        return "escalate"
    return "respond"


async def escalate_node(state: ConversationState) -> ConversationState:
    """Escalate to human support."""
    message = state.get("message", "")
    session_id = state.get("session_id", "")
    intent = state.get("intent", "")
    conversation_history = state.get("conversation_history", [])
    
    escalation_result = await escalate_to_human(
        message=message,
        session_id=session_id,
        intent=intent,
        conversation_history=conversation_history,
    )
    
    state["escalated"] = True
    state["escalation_ticket_id"] = escalation_result.get("ticket_id")
    state["response"] = escalation_result.get(
        "response",
        "I'm connecting you with a human agent who can better assist you.",
    )
    
    return state


def create_orchestrator_graph() -> StateGraph:
    """Create the LangGraph workflow."""
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("respond", respond_node)
    workflow.add_node("escalate", escalate_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Add edges
    workflow.add_edge("classify", "retrieve")
    workflow.add_edge("retrieve", "execute_tool")
    
    # Conditional edge after tool execution
    workflow.add_conditional_edges(
        "execute_tool",
        check_escalation,
        {
            "escalate": "escalate",
            "respond": "respond",
        },
    )
    
    # Final edges
    workflow.add_edge("escalate", END)
    workflow.add_edge("respond", END)
    
    return workflow.compile()


# Global orchestrator instance
orchestrator = create_orchestrator_graph()


async def process_message(
    message: str,
    session_id: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Process a user message through the orchestrator.
    
    Args:
        message: User's message
        session_id: Session identifier
        conversation_history: Previous conversation turns
        
    Returns:
        Dictionary with response and metadata
    """
    if conversation_history is None:
        conversation_history = []
    
    # Initialize state
    initial_state = ConversationState(
        message=message,
        session_id=session_id,
        conversation_history=conversation_history,
        escalated=False,
    )
    
    try:
        # Run through orchestrator
        result = await orchestrator.ainvoke(initial_state)
        
        return {
            "response": result.get("response", ""),
            "intent": result.get("intent", "unknown"),
            "tokens_used": result.get("tokens_used", 0),
            "escalated": result.get("escalated", False),
            "ticket_id": result.get("escalation_ticket_id"),
        }
    except Exception as e:
        logger.error(f"Error in orchestrator: {e}")
        # Fallback response
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact support directly.",
            "intent": "error",
            "tokens_used": 0,
            "escalated": True,
        }
