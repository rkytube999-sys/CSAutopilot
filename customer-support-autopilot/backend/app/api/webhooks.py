"""
Webhook endpoints for Shopify and Stripe integrations.
"""
import hashlib
import hmac
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Header

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def verify_shopify_hmac(payload: bytes, hmac_header: str) -> bool:
    """Verify Shopify webhook HMAC signature."""
    if not settings.shopify_access_token:
        return True  # Skip verification if not configured
    
    secret = settings.shopify_access_token.encode('utf-8')
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(digest, hmac_header)


@router.post("/shopify")
async def shopify_webhook(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None),
) -> Dict[str, Any]:
    """
    Handle Shopify webhooks.
    
    Receives order updates, product changes, etc.
    """
    body = await request.body()
    
    # Verify HMAC
    if not verify_shopify_hmac(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid HMAC")
    
    try:
        data = json.loads(body)
        topic = request.headers.get("x-shopify-topic", "unknown")
        
        logger.info(f"Received Shopify webhook: {topic}")
        
        # Store in Redis cache for quick access
        # In production, you'd sync to your database
        from app.integrations.redis_client import get_redis
        
        redis = await get_redis()
        if redis.initialized:
            order_id = data.get("id", "unknown")
            await redis.set(f"shopify:order:{order_id}", json.dumps(data), expire=3600)
        
        return {"status": "success", "topic": topic}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing Shopify webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def verify_stripe_signature(payload: bytes, sig_header: str) -> bool:
    """Verify Stripe webhook signature."""
    if not settings.stripe_webhook_secret:
        return True  # Skip verification if not configured
    
    try:
        import stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
        return True
    except Exception:
        return False


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
) -> Dict[str, Any]:
    """
    Handle Stripe webhooks.
    
    Receives payment events, refund confirmations, etc.
    """
    body = await request.body()
    
    # Verify signature
    if not verify_stripe_signature(body, stripe_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(body)
        event_type = data.get("type", "unknown")
        
        logger.info(f"Received Stripe webhook: {event_type}")
        
        # Handle different event types
        if event_type == "payment_intent.succeeded":
            # Payment successful
            pass
        elif event_type == "charge.refunded":
            # Refund processed
            pass
        
        return {"status": "success", "event_type": event_type}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
