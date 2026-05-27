"""
Email sending tools.

Handles sending email responses via SMTP or SendGrid.
"""
import logging
from typing import Dict, Any, Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
) -> Dict[str, Any]:
    """
    Send an email response.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        html: Whether body is HTML
        
    Returns:
        Send result dictionary
    """
    if not settings.email_smtp_pass:
        logger.warning("Email not configured, simulating send")
        return {
            "status": "simulated",
            "to": to,
            "subject": subject,
        }
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = "support@store.com"
        msg["To"] = to
        msg["Subject"] = subject
        
        # Attach body
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))
        
        # Send via SMTP
        await aiosmtplib.send(
            msg,
            hostname=settings.email_smtp_host,
            port=587,
            username=settings.email_smtp_user,
            password=settings.email_smtp_pass,
            start_tls=True,
        )
        
        logger.info(f"Email sent to {to}: {subject}")
        
        return {
            "status": "sent",
            "to": to,
            "subject": subject,
        }
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "to": to,
            "subject": subject,
        }
