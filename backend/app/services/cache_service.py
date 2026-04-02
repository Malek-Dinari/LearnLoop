"""
In-memory cache with TTL support.

Designed to be a drop-in replaced by a RedisCache later:
    class RedisCache:
        async def get(self, key): ...
        async def set(self, key, value, ttl): ...
        async def delete(self, key): ...
        async def clear(self): ...
    cache = RedisCache(url=settings.redis_url)

Just swap the singleton at the bottom of this file.
"""
import hashlib
import json
import logging
import time
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class CacheBackend(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int = 1800) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def clear(self) -> None: ...


class InMemoryCache:
    """Dict-based cache with TTL. Thread-safe for asyncio; not multiprocess-safe."""

    def __init__(self) -> None:
        # key -> (value, expires_at_monotonic)
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() < expires_at:
            logger.debug(f"Cache HIT: {key[:32]}...")
            return value
        # Expired — evict
        del self._store[key]
        logger.debug(f"Cache EXPIRED: {key[:32]}...")
        return None

    async def set(self, key: str, value: Any, ttl: int = 1800) -> None:
        self._store[key] = (value, time.monotonic() + ttl)
        logger.debug(f"Cache SET: {key[:32]}... (ttl={ttl}s, size={len(self._store)})")

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear(self) -> None:
        self._store.clear()
        logger.info("Cache cleared")

    @property
    def size(self) -> int:
        return len(self._store)


def make_cache_key(prefix: str, **kwargs: Any) -> str:
    """
    Generate a deterministic, short cache key from a prefix and keyword arguments.

    Example:
        make_cache_key("quiz", topic="photosynthesis", num=5, types=["mcq"])
        → "quiz:a3f1b2c4d5e6f7a8"
    """
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{prefix}:{digest}"


# Singleton — swap this with RedisCache when ready
cache: CacheBackend = InMemoryCache()
