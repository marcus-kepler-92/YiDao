"""
Redis Connection Module
"""

import logging

from redis import asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.redis_cache_url, encoding="utf8", decode_responses=True
        )
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
        redis_client = None
