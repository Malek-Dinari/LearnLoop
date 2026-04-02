import asyncio
import pytest
from app.services.cache_service import InMemoryCache, make_cache_key


@pytest.fixture
def cache():
    return InMemoryCache()


@pytest.mark.asyncio
async def test_set_get(cache):
    await cache.set("k1", {"data": 42}, ttl=60)
    result = await cache.get("k1")
    assert result == {"data": 42}


@pytest.mark.asyncio
async def test_get_missing(cache):
    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_ttl_expiry(cache):
    await cache.set("k_expire", "hello", ttl=0)
    # TTL=0 means already expired
    await asyncio.sleep(0.01)
    result = await cache.get("k_expire")
    assert result is None


@pytest.mark.asyncio
async def test_delete(cache):
    await cache.set("k_del", "value", ttl=60)
    await cache.delete("k_del")
    assert await cache.get("k_del") is None


@pytest.mark.asyncio
async def test_clear(cache):
    await cache.set("a", 1, ttl=60)
    await cache.set("b", 2, ttl=60)
    await cache.clear()
    assert cache.size == 0
    assert await cache.get("a") is None


def test_key_deterministic():
    k1 = make_cache_key("quiz", topic="photosynthesis", num=5)
    k2 = make_cache_key("quiz", topic="photosynthesis", num=5)
    assert k1 == k2


def test_key_different_inputs():
    k1 = make_cache_key("quiz", topic="photosynthesis", num=5)
    k2 = make_cache_key("quiz", topic="photosynthesis", num=10)
    assert k1 != k2


def test_key_order_independent():
    k1 = make_cache_key("quiz", topic="a", num=5)
    k2 = make_cache_key("quiz", num=5, topic="a")
    assert k1 == k2
