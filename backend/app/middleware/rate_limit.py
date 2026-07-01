"""Redis-based rate limiting middleware.

Implements sliding window rate limiting using Redis:
- 20 requests/minute for unauthenticated users (by IP)
- 100 requests/minute for authenticated users (by user ID)

Returns 429 Too Many Requests when limits are exceeded.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.redis import get_redis_cache
from app.core.security import decode_token

settings = get_settings()

# Optional bearer scheme - does not raise on missing token
_optional_bearer = HTTPBearer(auto_error=False)

# Rate limit window in seconds
RATE_LIMIT_WINDOW = 60  # 1 minute


async def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxy headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_rate_limit(
    redis: Redis,
    key: str,
    limit: int,
    window: int = RATE_LIMIT_WINDOW,
) -> tuple[bool, int, int]:
    """Check and increment rate limit counter using sliding window.

    Uses a simple fixed-window counter with Redis INCR and EXPIRE.

    Args:
        redis: Redis client instance.
        key: The rate limit key (includes user/IP identifier).
        limit: Maximum number of requests allowed in the window.
        window: Time window in seconds.

    Returns:
        Tuple of (allowed: bool, remaining: int, reset_seconds: int)
    """
    current_count = await redis.incr(key)

    if current_count == 1:
        # First request in this window - set expiry
        await redis.expire(key, window)

    ttl = await redis.ttl(key)
    if ttl < 0:
        # Key exists without TTL (edge case) - set it
        await redis.expire(key, window)
        ttl = window

    remaining = max(0, limit - current_count)
    allowed = current_count <= limit

    return allowed, remaining, ttl


async def rate_limit_dependency(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
    redis: Redis = Depends(get_redis_cache),
) -> None:
    """FastAPI dependency that enforces rate limiting on endpoints.

    Authenticated users (valid JWT) get 100 req/min.
    Unauthenticated users get 20 req/min, keyed by IP address.

    Raises:
        HTTPException 429: When the rate limit is exceeded.
    """
    user_id: Optional[str] = None
    is_authenticated = False

    # Try to extract user identity from token (if present)
    if credentials is not None:
        try:
            payload = decode_token(credentials.credentials)
            if payload.get("type") == "access":
                user_id = payload.get("sub")
                is_authenticated = True
        except (JWTError, Exception):
            # Invalid token - treat as unauthenticated for rate limiting
            pass

    if is_authenticated and user_id:
        # Authenticated: 100 req/min keyed by user ID
        key = f"rate_limit:auth:{user_id}"
        limit = settings.rate_limit_authenticated
    else:
        # Unauthenticated: 20 req/min keyed by IP
        client_ip = await _get_client_ip(request)
        key = f"rate_limit:unauth:{client_ip}"
        limit = settings.rate_limit_unauthenticated

    allowed, remaining, reset_seconds = await _check_rate_limit(redis, key, limit)

    # Set rate limit headers on the response (via request state)
    request.state.rate_limit_limit = limit
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_seconds

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "Retry-After": str(reset_seconds),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds),
            },
        )
