"""
Main FastAPI application entry point.

Sets up routers, middleware, and lifespan events.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import chat, email, webhooks
from app.integrations.vector_db import init_vector_db
from app.utils.logging import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Customer Support Autopilot...")
    
    # Initialize vector database
    try:
        await init_vector_db()
        logger.info("Vector database initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize vector database: {e}")
    
    logger.info("Customer Support Autopilot started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Customer Support Autopilot...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Customer Support Autopilot",
        description="AI-powered customer support resolution system",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(email.router, prefix="/api/email", tags=["email"])
    app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    # Stats endpoint for dashboard
    @app.get("/api/stats", tags=["stats"])
    async def get_stats(api_key: str):
        """Get analytics stats for dashboard."""
        if api_key != settings.admin_api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        try:
            # Get real analytics from database
            from app.core.fallback import get_analytics, get_recent_escalations
            
            analytics = await get_analytics()
            escalations = await get_recent_escalations(limit=10)
            
            # Format escalations (remove sensitive data)
            formatted_escalations = [
                {
                    "ticket_id": e["id"],
                    "session_id": e["session_id"],
                    "intent": e["intent"],
                    "sentiment": e["sentiment"],
                    "created_at": e["created_at"],
                    "status": e["status"],
                }
                for e in escalations
            ]
            
            return {
                "total_conversations": analytics["total_conversations"],
                "auto_resolution_rate": analytics["auto_resolution_rate"],
                "cost_per_resolution": analytics["cost_per_resolution"],
                "total_tokens_used": analytics["total_tokens_used"],
                "estimated_cost": analytics["estimated_cost"],
                "recent_escalations": formatted_escalations,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
