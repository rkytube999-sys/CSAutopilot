"""
Tests for the orchestrator module.
"""
import pytest
from app.core.orchestrator import process_message


@pytest.mark.asyncio
async def test_process_message_basic():
    """Test basic message processing."""
    result = await process_message(
        message="Hello, I need help with my order",
        session_id="test-session-123",
        conversation_history=[],
    )
    
    assert "response" in result
    assert "intent" in result
    assert isinstance(result["response"], str)


@pytest.mark.asyncio
async def test_process_message_refund_intent():
    """Test refund request classification."""
    result = await process_message(
        message="I want a refund for my order",
        session_id="test-session-456",
    )
    
    assert result["intent"] in ["refund_request", "faq"]


@pytest.mark.asyncio
async def test_process_message_order_status():
    """Test order status classification."""
    result = await process_message(
        message="Where is my order? When will it ship?",
        session_id="test-session-789",
    )
    
    assert result["intent"] in ["order_status", "faq"]
