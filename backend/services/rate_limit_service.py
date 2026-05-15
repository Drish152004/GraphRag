import logging
from inspect import isawaitable
from time import time_ns
from typing import Awaitable, Dict, List, Optional, Union

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from pyrate_limiter import Duration, Limiter, Rate, RateItem
from pyrate_limiter.abstracts import AbstractBucket, BucketFactory
from pyrate_limiter.buckets import InMemoryBucket, RedisBucket
from starlette.responses import Response

from backend.config import JWT_ALGORITHM, SECRET_KEY
from fastapi_limiter.depends import RateLimiter

logger = logging.getLogger("graphrag.ratelimit")

CHAT_REQUESTS_PER_MINUTE = 20
CHAT_RATE = Rate(CHAT_REQUESTS_PER_MINUTE, Duration.MINUTE)

_limiter: Optional[Limiter] = None
_chat_rate_limiter: Optional[RateLimiter] = None


class PerKeyRedisBucketFactory(BucketFactory):
    """Creates one Redis bucket per rate-limit key (per user / IP)."""

    def __init__(self, redis, rates: List[Rate], key_prefix: str = "graphrag:rl"):
        self.redis = redis
        self.rates = rates
        self.key_prefix = key_prefix
        self._buckets: Dict[str, RedisBucket] = {}

    def wrap_item(self, name: str, weight: int = 1) -> RateItem:
        now = time_ns() // 1_000_000
        return RateItem(name, now, weight=weight)

    def get(self, item: RateItem) -> Union[AbstractBucket, Awaitable[AbstractBucket]]:
        redis_key = f"{self.key_prefix}:{item.name}"

        if redis_key in self._buckets:
            return self._buckets[redis_key]

        init_result = RedisBucket.init(self.rates, self.redis, redis_key)

        if isawaitable(init_result):

            async def _resolve() -> AbstractBucket:
                if redis_key not in self._buckets:
                    bucket = await init_result
                    self._buckets[redis_key] = bucket
                    self.schedule_leak(bucket)
                return self._buckets[redis_key]

            return _resolve()

        self._buckets[redis_key] = init_result
        self.schedule_leak(init_result)
        return init_result


class _NoOpRateLimiter:
    async def __call__(self, request: Request, response: Response) -> None:
        return None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def _extract_user_id(request: Request) -> Optional[str]:
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.lower().startswith("bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
        user_id = str(subject).strip()
        return user_id or None
    except JWTError:
        return None
    except Exception:
        logger.debug("Rate limiter ignored malformed auth token")
        return None


async def rate_limit_identifier(request: Request) -> str:
    """
  Rate-limit key priority:
  1. Authenticated user id  -> rate_limit:user_{id}
  2. Client IP fallback    -> rate_limit:ip_{ip}
    """
    user_id = _extract_user_id(request)
    if user_id:
        return f"rate_limit:user_{user_id}"
    return f"rate_limit:ip_{_client_ip(request)}"


async def rate_limit_exceeded_callback(request: Request, response: Response) -> None:
    key = await rate_limit_identifier(request)
    logger.warning("Rate limit triggered | key=%s", key)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Please try again later.",
    )


class FastAPILimiter:
    """
    Redis-backed limiter bootstrap for fastapi-limiter 0.2.x.
    (Replaces the removed fastapi_limiter.FastAPILimiter Redis initializer.)
    """

    redis = None
    limiter: Optional[Limiter] = None

    @classmethod
    async def init(cls, redis_client) -> bool:
        global _limiter, _chat_rate_limiter

        cls.redis = redis_client
        factory = PerKeyRedisBucketFactory(redis_client, [CHAT_RATE])
        cls.limiter = Limiter(factory)
        _limiter = cls.limiter
        _chat_rate_limiter = RateLimiter(
            limiter=_limiter,
            identifier=rate_limit_identifier,
            callback=rate_limit_exceeded_callback,
            blocking=False,
        )
        logger.info(
            "Rate limiter initialized | limit=%d/minute | backend=redis",
            CHAT_REQUESTS_PER_MINUTE,
        )
        return True

    @classmethod
    async def init_disabled(cls) -> None:
        """Fail open with in-memory limiter when Redis is unavailable."""
        global _limiter, _chat_rate_limiter

        bucket = InMemoryBucket([CHAT_RATE])
        _limiter = Limiter(bucket)
        _chat_rate_limiter = RateLimiter(
            limiter=_limiter,
            identifier=rate_limit_identifier,
            callback=rate_limit_exceeded_callback,
            blocking=False,
        )
        logger.warning(
            "Rate limiter using in-memory fallback (not distributed); "
            "set REDIS_URL for Redis Cloud"
        )


def get_chat_rate_limiter():
    if _chat_rate_limiter is None:
        return _NoOpRateLimiter()
    return _chat_rate_limiter


async def shutdown_rate_limiter() -> None:
    """Release limiter references on app shutdown."""
    global _limiter, _chat_rate_limiter

    _chat_rate_limiter = None
    _limiter = None
    FastAPILimiter.redis = None
    FastAPILimiter.limiter = None


async def enforce_chat_rate_limit(request: Request, response: Response) -> None:
    """FastAPI dependency wrapper (limiter is bound during app startup)."""
    try:
        limiter = get_chat_rate_limiter()
        await limiter(request, response)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Rate limiter internal error (%s); allowing request",
            type(exc).__name__,
        )
