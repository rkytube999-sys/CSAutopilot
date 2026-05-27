"""
Shopify integration tools.

Handles order lookup and customer data retrieval.
"""
import logging
from typing import Dict, Any, Optional, List

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_order_info(order_id: str) -> Dict[str, Any]:
    """
    Look up order information from Shopify.
    
    Args:
        order_id: Shopify order ID
        
    Returns:
        Order information dictionary
    """
    if not settings.use_shopify:
        return {
            "error": "Shopify integration not configured",
            "order_id": order_id,
        }
    
    try:
        url = f"{settings.shopify_store_url}/admin/api/2024-01/orders/{order_id}.json"
        
        headers = {
            "X-Shopify-Access-Token": settings.shopify_access_token,
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                order = data.get("order", {})
                
                return {
                    "order_id": order.get("id"),
                    "order_number": order.get("order_number"),
                    "status": order.get("financial_status"),
                    "fulfillment_status": order.get("fulfillment_status"),
                    "total": order.get("total_price"),
                    "currency": order.get("currency"),
                    "items": [
                        {
                            "name": item.get("title"),
                            "quantity": item.get("quantity"),
                            "price": item.get("price"),
                        }
                        for item in order.get("line_items", [])
                    ],
                    "shipping_address": order.get("shipping_address"),
                    "created_at": order.get("created_at"),
                }
            else:
                logger.warning(f"Shopify API error: {response.status_code}")
                return {
                    "error": f"Order not found or API error: {response.status_code}",
                    "order_id": order_id,
                }
                
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Shopify: {e}")
        return {"error": f"Network error: {str(e)}", "order_id": order_id}
    except Exception as e:
        logger.error(f"Error getting order info: {e}")
        return {"error": str(e), "order_id": order_id}


async def get_customer_orders(email: str) -> List[Dict[str, Any]]:
    """
    Get all orders for a customer by email.
    
    Args:
        email: Customer email address
        
    Returns:
        List of order dictionaries
    """
    if not settings.use_shopify:
        return []
    
    try:
        url = f"{settings.shopify_store_url}/admin/api/2024-01/orders.json"
        params = {"email": email}
        
        headers = {
            "X-Shopify-Access-Token": settings.shopify_access_token,
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                
                return [
                    {
                        "order_id": order.get("id"),
                        "order_number": order.get("order_number"),
                        "status": order.get("financial_status"),
                        "total": order.get("total_price"),
                        "created_at": order.get("created_at"),
                    }
                    for order in orders
                ]
            else:
                logger.warning(f"Shopify API error: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"Error getting customer orders: {e}")
        return []
