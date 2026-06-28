"""Redis connection configuration for caching and session storage."""

from redis.asyncio import Redis, ConnectionPool

from app.core.config import get_settings

settings = get_settings()

# Connection pool for general cache operations
_cache_pool: ConnectionPool | None = None

# Connection pool for session storage
_session_pool: ConnectionPool | None = None


def get_cache_pool() -> ConnectionPool:
    """Get or create Redis connection pool for caching."""
    global _cache_pool
    if _cache_pool is None:
        _cache_pool = ConnectionPool.from_url(
            settings.redis_url,
            db=settings.redis_cache_db,
            max_connections=20,
            decode_responses=True,
        )
    return _cache_pool


def get_session_pool() -> ConnectionPool:
    """Get or create Redis connection pool for session storage."""
    global _session_pool
    if _session_pool is None:
        _session_pool = ConnectionPool.from_url(
            settings.redis_url,
            db=settings.redis_session_db,
            max_connections=20,
            decode_responses=True,
        )
    return _session_pool


async def get_redis_cache() -> Redis:
    """Dependency that provides a Redis client for caching."""
    pool = get_cache_pool()
    return Redis(connection_pool=pool)


async def get_redis_session() -> Redis:
    """Dependency that provides a Redis client for session storage."""
    pool = get_session_pool()
    return Redis(connection_pool=pool)


async def close_redis() -> None:
    """Close all Redis connection pools."""
    global _cache_pool, _session_pool
    if _cache_pool is not None:
        await _cache_pool.aclose()
        _cache_pool = None
    if _session_pool is not None:
        await _session_pool.aclose()
        _session_pool = None
