"""
Groq LLM client for text generation and embeddings.
"""
import logging
from typing import Optional, List

from groq import Groq
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Groq client
groq_client = None
if settings.groq_api_key:
    groq_client = Groq(api_key=settings.groq_api_key)


async def call_groq_llm(
    prompt: str,
    system_message: str = "You are a helpful customer support assistant.",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Call Groq LLM for text generation.
    
    Args:
        prompt: User prompt
        system_message: System instruction
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Generated text response
    """
    if not groq_client:
        logger.warning("Groq client not initialized, using fallback")
        return _fallback_response(prompt)
    
    try:
        response = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content or ""
        
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return _fallback_response(prompt)


async def generate_response(
    message: str,
    intent: str,
    context: Optional[List[dict]] = None,
    tool_result: Optional[dict] = None,
    conversation_history: Optional[List[dict]] = None,
) -> dict:
    """
    Generate a customer support response using Groq.
    
    Args:
        message: User's message
        intent: Classified intent
        context: Retrieved knowledge base chunks
        tool_result: Result from tool execution
        conversation_history: Previous conversation
        
    Returns:
        Dictionary with response and token usage
    """
    # Build context string
    context_str = ""
    if context:
        context_str = "\n\nRelevant information:\n"
        for chunk in context:
            context_str += f"- {chunk.get('text', '')}\n"
    
    # Add tool result if available
    if tool_result:
        context_str += f"\n\nTool result: {tool_result}\n"
    
    # Build prompt
    system_prompt = f"""You are a helpful customer support assistant for an e-commerce store.
Your goal is to resolve customer inquiries quickly and accurately.

Intent: {intent}
{context_str}

Guidelines:
- Be friendly and professional
- Provide clear, concise answers
- If you don't know something, admit it and offer to connect with human support
- For order issues, ask for order ID if not provided
- For refunds, explain the refund policy
"""

    # Format conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_history:
        for turn in conversation_history[-5:]:
            messages.append(turn)
    
    messages.append({"role": "user", "content": message})
    
    try:
        if not groq_client:
            response_text = _fallback_response(message)
            return {"response": response_text, "tokens_used": 0}
        
        response = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0.7,
            max_tokens=512,
        )
        
        response_text = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        return {"response": response_text, "tokens_used": tokens_used}
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again.",
            "tokens_used": 0,
        }


def _fallback_response(message: str) -> str:
    """Simple fallback response when Groq is unavailable."""
    return (
        "Thank you for your message. This is a demo response - please configure your Groq API key "
        "in the .env file to enable full AI-powered responses. "
        f"You said: '{message[:100]}...'"
    )


async def embed_text(text: str) -> List[float]:
    """
    Generate embedding for text.
    
    Note: Groq doesn't currently support embeddings, so we use a simple hash-based
    approach for demo purposes. In production, use a proper embedding model.
    """
    # Simple hash-based pseudo-embedding for demo
    # In production, use sentence-transformers or similar
    import hashlib
    
    # Create a deterministic 384-dimensional vector (compatible with most models)
    hash_input = text.encode('utf-8')
    hash_bytes = hashlib.sha256(hash_input).digest()
    
    # Expand to 384 dimensions using multiple hashes
    embedding = []
    for i in range(384):
        seed = hash_bytes[i % len(hash_bytes)] + i
        value = (hashlib.md5(bytes([seed])).digest()[0] - 128) / 128.0
        embedding.append(float(value))
    
    return embedding
