"""
Intent classifier using Groq LLM.

Classifies user messages into: refund_request, order_status, faq, human_escalation.
"""
import logging
import json
from typing import Dict, Any, List, Optional

from app.config import get_settings
from app.integrations.groq_client import call_groq_llm

logger = logging.getLogger(__name__)
settings = get_settings()


CLASSIFICATION_PROMPT = """
You are an intent classifier for customer support. Classify the user's message into one of these categories:

1. **refund_request**: User is asking for a refund or return
2. **order_status**: User wants to know about their order status, shipping, or delivery
3. **faq**: General question about products, policies, or services
4. **human_escalation**: User is upset, frustrated, or explicitly requests human agent

Also assess the sentiment: positive, neutral, or negative.

Message: {message}

Conversation History: {history}

Respond with ONLY a JSON object in this format:
{{
    "intent": "one_of_the_four_categories",
    "confidence": 0.0_to_1.0,
    "sentiment": "positive|neutral|negative",
    "reasoning": "brief explanation"
}}
"""


async def classify_intent(
    message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Classify the intent of a user message.
    
    Args:
        message: The user's message
        conversation_history: Previous conversation turns
        
    Returns:
        Dictionary with intent, confidence, and sentiment
    """
    if conversation_history is None:
        conversation_history = []
    
    # Format conversation history
    history_str = ""
    if conversation_history:
        for turn in conversation_history[-5:]:  # Last 5 turns
            role = turn.get("role", "user")
            content = turn.get("content", "")
            history_str += f"{role}: {content}\n"
    
    # If no history, indicate that
    if not history_str:
        history_str = "No previous conversation."
    
    # Create prompt
    prompt = CLASSIFICATION_PROMPT.format(
        message=message,
        history=history_str,
    )
    
    try:
        # Call Groq LLM
        response = await call_groq_llm(
            prompt=prompt,
            system_message="You are an intent classifier. Respond only with valid JSON.",
            temperature=0.0,  # Low temperature for consistent classification
        )
        
        # Parse JSON response
        result = json.loads(response)
        
        # Validate result
        valid_intents = ["refund_request", "order_status", "faq", "human_escalation"]
        valid_sentiments = ["positive", "neutral", "negative"]
        
        intent = result.get("intent", "faq")
        if intent not in valid_intents:
            intent = "faq"
            
        sentiment = result.get("sentiment", "neutral")
        if sentiment not in valid_sentiments:
            sentiment = "neutral"
        
        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        return {
            "intent": intent,
            "confidence": confidence,
            "sentiment": sentiment,
            "reasoning": result.get("reasoning", ""),
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse classification response: {e}")
        logger.debug(f"Raw response: {response}")
        # Fallback to FAQ with low confidence
        return {
            "intent": "faq",
            "confidence": 0.3,
            "sentiment": "neutral",
            "reasoning": "Failed to parse classification, defaulting to FAQ",
        }
    except Exception as e:
        logger.error(f"Error in intent classification: {e}")
        # Fallback without Groq
        return _fallback_classification(message)


def _fallback_classification(message: str) -> Dict[str, Any]:
    """
    Simple keyword-based fallback classification when Groq is unavailable.
    """
    message_lower = message.lower()
    
    # Refund keywords
    refund_keywords = ["refund", "return", "money back", "reimburse", "chargeback"]
    if any(keyword in message_lower for keyword in refund_keywords):
        return {
            "intent": "refund_request",
            "confidence": 0.6,
            "sentiment": "neutral",
            "reasoning": "Keyword match (fallback)",
        }
    
    # Order status keywords
    order_keywords = ["order", "shipping", "delivery", "track", "status", "where is my"]
    if any(keyword in message_lower for keyword in order_keywords):
        return {
            "intent": "order_status",
            "confidence": 0.6,
            "sentiment": "neutral",
            "reasoning": "Keyword match (fallback)",
        }
    
    # Escalation keywords
    escalation_keywords = ["human", "agent", "representative", "complaint", "angry", "frustrated", "unhappy"]
    if any(keyword in message_lower for keyword in escalation_keywords):
        return {
            "intent": "human_escalation",
            "confidence": 0.5,
            "sentiment": "negative",
            "reasoning": "Keyword match (fallback)",
        }
    
    # Default to FAQ
    return {
        "intent": "faq",
        "confidence": 0.5,
        "sentiment": "neutral",
        "reasoning": "Default classification (fallback)",
    }
