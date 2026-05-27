"""
Stripe integration tools.

Handles payment and refund operations.
"""
import logging
from typing import Dict, Any

import stripe

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


async def process_refund(
    payment_intent_id: str,
    amount: int,
    reason: str = "",
) -> Dict[str, Any]:
    """
    Process a refund through Stripe.
    
    Args:
        payment_intent_id: Stripe Payment Intent ID
        amount: Amount to refund in cents
        reason: Reason for refund
        
    Returns:
        Refund result dictionary
    """
    if not settings.use_stripe:
        return {
            "error": "Stripe integration not configured",
            "payment_intent_id": payment_intent_id,
            "simulated": True,
        }
    
    try:
        # Create refund
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=amount,
            reason=reason if reason else "requested_by_customer",
        )
        
        return {
            "refund_id": refund.id,
            "amount": refund.amount,
            "currency": refund.currency,
            "status": refund.status,
            "reason": refund.reason,
            "payment_intent_id": payment_intent_id,
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return {
            "error": f"Stripe error: {str(e)}",
            "payment_intent_id": payment_intent_id,
        }
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        return {"error": str(e), "payment_intent_id": payment_intent_id}


async def get_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """
    Retrieve payment intent information.
    
    Args:
        payment_intent_id: Stripe Payment Intent ID
        
    Returns:
        Payment intent information
    """
    if not settings.use_stripe:
        return {"error": "Stripe integration not configured"}
    
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        return {
            "id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
            "customer": intent.customer,
            "created": intent.created,
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return {"error": f"Stripe error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error getting payment intent: {e}")
        return {"error": str(e)}
