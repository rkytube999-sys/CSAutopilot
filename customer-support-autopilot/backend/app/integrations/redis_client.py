"""
Redis client for session storage and rate limiting.
"""
import logging
from typing import Optional

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    """Async Redis client wrapper."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        try:
            self.client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.client.ping()
            self.initialized = True
            logger.info("Redis connection established")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.initialized = False
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self.initialized or not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Set value in Redis with expiration."""
        if not self.initialized or not self.client:
            return False
        try:
            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def incr(self, key: str) -> int:
        """Increment a counter."""
        if not self.initialized or not self.client:
            return 0
        try:
            return await self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        if not self.initialized or not self.client:
            return False
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False


# Global Redis client
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Get initialized Redis client."""
    if not redis_client.initialized:
        await redis_client.initialize()
    return redis_client
