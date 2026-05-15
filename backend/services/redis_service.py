import logging
from typing import Optional
from urllib.parse import urlparse

import redis.asyncio as aioredis

from backend.config import REDIS_URL

logger = logging.getLogger("graphrag.redis")

redis_client: Optional[aioredis.Redis] = None


def _redis_target_label() -> str:
    """Log-friendly target without credentials."""
    if not REDIS_URL:
        return "not configured"
    parsed = urlparse(REDIS_URL)
    host = parsed.hostname or "unknown-host"
    port = parsed.port or 6379
    scheme = parsed.scheme or "redis"
    return f"{scheme}://{host}:{port}"


async def init_redis() -> Optional[aioredis.Redis]:
    """Initialize async Redis client from REDIS_URL (supports redis:// and rediss://)."""
    global redis_client

    if not REDIS_URL:
        logger.warning("REDIS_URL is not set; rate limiting will use in-memory fallback")
        return None

    try:
        client = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await client.ping()
        redis_client = client
        logger.info("Redis connected successfully | target=%s", _redis_target_label())
        return redis_client
    except Exception as exc:
        logger.error(
            "Redis connection failed | target=%s | error=%s",
            _redis_target_label(),
            type(exc).__name__,
        )
        redis_client = None
        return None


async def close_redis() -> None:
    """Close Redis client and release the connection pool."""
    global redis_client

    if redis_client is None:
        return

    client = redis_client
    redis_client = None

    try:
        await client.aclose()
        logger.info("Redis connection closed")
    except Exception as exc:
        logger.warning("Redis close error (%s)", type(exc).__name__)


def get_redis_client() -> Optional[aioredis.Redis]:
    return redis_client
