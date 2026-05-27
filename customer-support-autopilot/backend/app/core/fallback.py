"""
Fallback and escalation handler.

Handles cases where the AI cannot resolve the issue and needs to escalate to human support.
"""
import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database path for escalations
DB_PATH = Path("/app/data/escalations.db")


def _get_db_connection():
    """Get SQLite database connection."""
    # Ensure directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_escalation_db():
    """Initialize the escalations database."""
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                intent TEXT,
                message TEXT NOT NULL,
                conversation_history TEXT,
                sentiment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                resolved_at TIMESTAMP,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                tokens_used INTEGER,
                endpoint TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Escalation database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize escalation database: {e}")


async def escalate_to_human(
    message: str,
    session_id: str,
    intent: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    sentiment: str = "neutral",
) -> Dict[str, Any]:
    """
    Create an escalation ticket for human support.
    
    Args:
        message: Current user message
        session_id: Session identifier
        intent: Classified intent
        conversation_history: Full conversation history
        sentiment: User sentiment
        
    Returns:
        Ticket information and response message
    """
    import json
    
    # Generate ticket ID
    ticket_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        # Store in database
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO escalations 
            (id, session_id, intent, message, conversation_history, sentiment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                session_id,
                intent,
                message,
                json.dumps(conversation_history or []),
                sentiment,
            ),
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created escalation ticket: {ticket_id}")
        
        # In production, you would also:
        # - Send notification to support team (Slack, email, etc.)
        # - Create ticket in Zendesk/Freshdesk if configured
        # - Send confirmation email to customer
        
        return {
            "ticket_id": ticket_id,
            "status": "created",
            "response": (
                f"I understand you need additional assistance. "
                f"I've created ticket {ticket_id} and a human agent will review your case shortly. "
                f"We typically respond within 24 hours."
            ),
        }
        
    except Exception as e:
        logger.error(f"Failed to create escalation ticket: {e}")
        
        # Return graceful error response
        return {
            "ticket_id": None,
            "status": "failed",
            "response": (
                "I apologize, but I'm unable to create a ticket at the moment. "
                "Please contact our support team directly at support@example.com."
            ),
        }


async def log_token_usage(
    session_id: str,
    tokens_used: int,
    endpoint: str = "chat",
) -> None:
    """Log token usage for analytics."""
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO token_usage (session_id, tokens_used, endpoint)
            VALUES (?, ?, ?)
            """,
            (session_id, tokens_used, endpoint),
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log token usage: {e}")


async def get_recent_escalations(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent escalation tickets."""
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM escalations 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (limit,),
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Failed to get recent escalations: {e}")
        return []


async def get_analytics() -> Dict[str, Any]:
    """Get analytics data for dashboard."""
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        # Total conversations (approximate from token usage)
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM token_usage")
        total_conversations = cursor.fetchone()[0] or 0
        
        # Total escalations
        cursor.execute("SELECT COUNT(*) FROM escalations")
        total_escalations = cursor.fetchone()[0] or 0
        
        # Auto-resolution rate
        if total_conversations > 0:
            auto_resolution_rate = (
                (total_conversations - total_escalations) / total_conversations
            ) * 100
        else:
            auto_resolution_rate = 0.0
        
        # Total tokens used
        cursor.execute("SELECT SUM(tokens_used) FROM token_usage")
        total_tokens = cursor.fetchone()[0] or 0
        
        # Estimated cost (assuming $0.0007 per 1K tokens for Groq)
        estimated_cost = (total_tokens / 1000) * 0.0007
        
        # Cost per resolution
        if total_conversations > 0:
            cost_per_resolution = estimated_cost / total_conversations
        else:
            cost_per_resolution = 0.0
        
        conn.close()
        
        return {
            "total_conversations": total_conversations,
            "total_escalations": total_escalations,
            "auto_resolution_rate": round(auto_resolution_rate, 2),
            "total_tokens_used": total_tokens,
            "estimated_cost": round(estimated_cost, 4),
            "cost_per_resolution": round(cost_per_resolution, 6),
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        return {
            "total_conversations": 0,
            "total_escalations": 0,
            "auto_resolution_rate": 0.0,
            "total_tokens_used": 0,
            "estimated_cost": 0.0,
            "cost_per_resolution": 0.0,
        }


# Initialize database on module load
init_escalation_db()
