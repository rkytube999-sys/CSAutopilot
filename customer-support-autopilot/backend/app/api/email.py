"""
Email API endpoint for auto-responder.

Accepts email JSON and processes through the same orchestrator as chat.
"""
import logging
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.orchestrator import process_message
from app.tools.email_tools import send_email

logger = logging.getLogger(__name__)

router = APIRouter()


class EmailRequest(BaseModel):
    """Request model for email endpoint."""
    from_email: str
    subject: str
    body: str
    to_email: Optional[str] = None  # For replies


class EmailResponse(BaseModel):
    """Response model for email endpoint."""
    status: str
    session_id: str
    response_sent: bool
    message: str


@router.post("/", response_model=EmailResponse)
async def email_handler(request: EmailRequest) -> EmailResponse:
    """
    Process an incoming email and send auto-response.
    
    This endpoint accepts email data (typically from a webhook like SendGrid),
    processes it through the same AI orchestrator as chat, and sends a reply.
    """
    # Generate session ID based on sender email
    session_id = f"email-{request.from_email}-{uuid.uuid4().hex[:8]}"
    
    try:
        # Process through orchestrator
        result = await process_message(
            message=f"Subject: {request.subject}\n\n{request.body}",
            session_id=session_id,
            conversation_history=[],
        )
        
        # Determine recipient (reply to sender by default)
        recipient = request.to_email or request.from_email
        
        # Send email response
        email_result = await send_email(
            to=recipient,
            subject=f"Re: {request.subject}",
            body=result["response"],
            html=False,
        )
        
        response_sent = email_result.get("status") in ["sent", "simulated"]
        
        return EmailResponse(
            status="processed",
            session_id=session_id,
            response_sent=response_sent,
            message=f"Email processed and {'response sent' if response_sent else 'response simulated'}",
        )
        
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process email: {str(e)}")
