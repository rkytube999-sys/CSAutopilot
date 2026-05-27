"""
Rate limiter using Redis sliding window algorithm.
"""
import logging
import time
from typing import Tuple

from app.config import get_settings
from app.integrations.redis_client import get_redis

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """Sliding window rate limiter."""
    
    def __init__(self):
        self.max_requests = settings.rate_limit_requests
        self.window_seconds = settings.rate_limit_window
    
    async def check_rate_limit(self, session_id: str) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Tuple of (allowed, remaining_requests)
            
        Raises:
            RateLimitExceeded: If limit is exceeded
        """
        redis = await get_redis()
        
        if not redis.initialized:
            # If Redis not available, allow all requests
            return True, self.max_requests
        
        key = f"rate_limit:{session_id}"
        current_time = int(time.time())
        window_key = f"{key}:{current_time // self.window_seconds}"
        
        try:
            # Get current count
            current_count = await redis.client.get(window_key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= self.max_requests:
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Try again in {self.window_seconds} seconds."
                )
            
            # Increment counter
            await redis.client.incr(window_key)
            await redis.client.expire(window_key, self.window_seconds * 2)
            
            remaining = self.max_requests - current_count - 1
            
            return True, remaining
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, self.max_requests


# Global rate limiter instance
rate_limiter = RateLimiter()
