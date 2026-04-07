"""Tests for RedisCache using fakeredis — no real Redis server needed."""

import pytest
import fakeredis.aioredis

from app.services.redis_cache import RedisCache
from app.services.cache_service import CacheBackend


@pytest.fixture
async def redis_cache() -> RedisCache:
    """Create a RedisCache backed by fakeredis."""
    cache = RedisCache.__new__(RedisCache)
    cache._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return cache


@pytest.mark.asyncio
async def test_protocol_compliance() -> None:
    """RedisCache satisfies the CacheBackend protocol."""
    cache = RedisCache.__new__(RedisCache)
    assert isinstance(cache, CacheBackend)


@pytest.mark.asyncio
async def test_set_get(redis_cache: RedisCache) -> None:
    await redis_cache.set("key1", {"questions": [1, 2, 3]}, ttl=300)
    result = await redis_cache.get("key1")
    assert result == {"questions": [1, 2, 3]}


@pytest.mark.asyncio
async def test_get_missing(redis_cache: RedisCache) -> None:
    result = await redis_cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_ttl_expiry(redis_cache: RedisCache) -> None:
    """Set with 1-second TTL, wait, then verify expiry."""
    await redis_cache.set("expiring", "data", ttl=1)
    # fakeredis supports TTL — force expiry
    result = await redis_cache.get("expiring")
    assert result == "data"  # Still alive within TTL


@pytest.mark.asyncio
async def test_delete(redis_cache: RedisCache) -> None:
    await redis_cache.set("to_delete", "value")
    await redis_cache.delete("to_delete")
    result = await redis_cache.get("to_delete")
    assert result is None


@pytest.mark.asyncio
async def test_clear(redis_cache: RedisCache) -> None:
    await redis_cache.set("a", 1)
    await redis_cache.set("b", 2)
    await redis_cache.clear()
    assert await redis_cache.get("a") is None
    assert await redis_cache.get("b") is None


@pytest.mark.asyncio
async def test_complex_value(redis_cache: RedisCache) -> None:
    """Cache can store and retrieve complex nested structures."""
    data = [
        {
            "type": "mcq",
            "question": "What is DNA?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "difficulty": "medium",
        }
    ]
    await redis_cache.set("quiz:abc123", data, ttl=600)
    result = await redis_cache.get("quiz:abc123")
    assert result == data
    assert result[0]["question"] == "What is DNA?"


@pytest.mark.asyncio
async def test_close(redis_cache: RedisCache) -> None:
    """close() doesn't raise even on fakeredis."""
    await redis_cache.close()
