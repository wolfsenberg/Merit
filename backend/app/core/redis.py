"""Redis connection configuration for caching and session storage.

Falls back to a no-op mock when Redis is not available (local dev without Docker).
"""

from redis.asyncio import ConnectionPool, Redis

from app.core.config import get_settings

settings = get_settings()

_cache_pool: ConnectionPool | None = None
_session_pool: ConnectionPool | None = None
_redis_available: bool | None = None


class MockRedis:
    """No-op Redis mock for local development without Redis."""

    async def incr(self, key: str) -> int:
        return 1

    async def expire(self, key: str, seconds: int) -> None:
        pass

    async def ttl(self, key: str) -> int:
        return -2  # Key doesn't exist

    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        pass

    async def delete(self, *keys: str) -> None:
        pass

    async def exists(self, key: str) -> int:
        return 0


async def _check_redis() -> bool:
    """Check if Redis is reachable."""
    global _redis_available
    if _redis_available is not None:
        return _redis_available
    try:
        pool = ConnectionPool.from_url(settings.redis_url, db=0, max_connections=1)
        client = Redis(connection_pool=pool)
        await client.ping()
        await pool.aclose()
        _redis_available = True
    except Exception:
        _redis_available = False
    return _redis_available


def get_cache_pool() -> ConnectionPool:
    global _cache_pool
    if _cache_pool is None:
        _cache_pool = ConnectionPool.from_url(
            settings.redis_url, db=settings.redis_cache_db, max_connections=20, decode_responses=True,
        )
    return _cache_pool


def get_session_pool() -> ConnectionPool:
    global _session_pool
    if _session_pool is None:
        _session_pool = ConnectionPool.from_url(
            settings.redis_url, db=settings.redis_session_db, max_connections=20, decode_responses=True,
        )
    return _session_pool


async def get_redis_cache() -> Redis | MockRedis:
    """Dependency that provides a Redis client for caching. Falls back to mock."""
    if not await _check_redis():
        return MockRedis()  # type: ignore
    pool = get_cache_pool()
    return Redis(connection_pool=pool)


async def get_redis_session() -> Redis | MockRedis:
    """Dependency that provides a Redis client for session storage. Falls back to mock."""
    if not await _check_redis():
        return MockRedis()  # type: ignore
    pool = get_session_pool()
    return Redis(connection_pool=pool)


async def close_redis() -> None:
    global _cache_pool, _session_pool
    if _cache_pool is not None:
        try:
            await _cache_pool.aclose()
        except Exception:
            pass
        _cache_pool = None
    if _session_pool is not None:
        try:
            await _session_pool.aclose()
        except Exception:
            pass
        _session_pool = None
