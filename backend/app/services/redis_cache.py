"""Redis-backed cache implementing the CacheBackend protocol."""

import json
import logging
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache with JSON serialization and TTL support.

    All methods are fault-tolerant: Redis failures log a warning
    and return gracefully (None for get, no-op for set/delete/clear).
    The application must never crash because Redis is unavailable.
    """

    def __init__(self, url: str) -> None:
        self._redis: redis.Redis = redis.from_url(  # type: ignore[assignment]
            url, decode_responses=True
        )

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            logger.debug(f"Cache HIT: {key[:32]}...")
            return json.loads(raw)
        except redis.ConnectionError as exc:
            logger.warning(f"Redis connection error on GET: {exc}")
            return None
        except Exception as exc:
            logger.warning(f"Redis GET error: {exc}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 1800) -> None:
        try:
            serialized = json.dumps(value, default=str)
            await self._redis.set(key, serialized, ex=ttl)
            logger.debug(f"Cache SET: {key[:32]}... (ttl={ttl}s)")
        except redis.ConnectionError as exc:
            logger.warning(f"Redis connection error on SET: {exc}")
        except Exception as exc:
            logger.warning(f"Redis SET error: {exc}")

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except redis.ConnectionError as exc:
            logger.warning(f"Redis connection error on DELETE: {exc}")
        except Exception as exc:
            logger.warning(f"Redis DELETE error: {exc}")

    async def clear(self) -> None:
        try:
            await self._redis.flushdb()
            logger.info("Cache cleared (Redis flushdb)")
        except redis.ConnectionError as exc:
            logger.warning(f"Redis connection error on CLEAR: {exc}")
        except Exception as exc:
            logger.warning(f"Redis CLEAR error: {exc}")

    async def close(self) -> None:
        """Close the Redis connection pool. Called on app shutdown."""
        try:
            await self._redis.aclose()
        except Exception:
            pass
