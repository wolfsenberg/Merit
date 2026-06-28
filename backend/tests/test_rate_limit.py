"""Tests for Redis-based rate limiting middleware."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Depends, status
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.core.config import get_settings
from app.core.security import create_access_token
from app.middleware.rate_limit import (
    RATE_LIMIT_WINDOW,
    _check_rate_limit,
    _get_client_ip,
    rate_limit_dependency,
)

settings = get_settings()


# ============================================================
# Unit Tests for Rate Limit Helpers
# ============================================================


class TestGetClientIP:
    """Tests for client IP extraction."""

    @pytest.mark.asyncio
    async def test_extracts_ip_from_x_forwarded_for(self):
        """Should use X-Forwarded-For header when present."""
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        ip = await _get_client_ip(request)
        assert ip == "203.0.113.50"

    @pytest.mark.asyncio
    async def test_falls_back_to_client_host(self):
        """Should use request.client.host when no proxy header."""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        ip = await _get_client_ip(request)
        assert ip == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_handles_missing_client(self):
        """Should return 'unknown' when client is None."""
        request = MagicMock()
        request.headers = {}
        request.client = None

        ip = await _get_client_ip(request)
        assert ip == "unknown"


class TestCheckRateLimit:
    """Tests for the rate limit checking logic."""

    @pytest.mark.asyncio
    async def test_allows_request_under_limit(self):
        """Should allow requests when count is under the limit."""
        redis = AsyncMock()
        redis.incr.return_value = 1
        redis.ttl.return_value = 60

        allowed, remaining, reset = await _check_rate_limit(redis, "test:key", limit=20)

        assert allowed is True
        assert remaining == 19
        assert reset == 60

    @pytest.mark.asyncio
    async def test_blocks_request_over_limit(self):
        """Should block requests when count exceeds the limit."""
        redis = AsyncMock()
        redis.incr.return_value = 21
        redis.ttl.return_value = 45

        allowed, remaining, reset = await _check_rate_limit(redis, "test:key", limit=20)

        assert allowed is False
        assert remaining == 0
        assert reset == 45

    @pytest.mark.asyncio
    async def test_sets_expire_on_first_request(self):
        """Should set TTL on the key when it's the first request."""
        redis = AsyncMock()
        redis.incr.return_value = 1
        redis.ttl.return_value = 60

        await _check_rate_limit(redis, "test:key", limit=20, window=60)

        redis.expire.assert_called_once_with("test:key", 60)

    @pytest.mark.asyncio
    async def test_does_not_set_expire_on_subsequent_requests(self):
        """Should not set TTL on subsequent requests."""
        redis = AsyncMock()
        redis.incr.return_value = 5
        redis.ttl.return_value = 42

        await _check_rate_limit(redis, "test:key", limit=20)

        redis.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_at_exact_limit_is_allowed(self):
        """Request at exactly the limit should still be allowed."""
        redis = AsyncMock()
        redis.incr.return_value = 20
        redis.ttl.return_value = 30

        allowed, remaining, reset = await _check_rate_limit(redis, "test:key", limit=20)

        assert allowed is True
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_handles_negative_ttl(self):
        """Should set expire when TTL is negative (key without expiry)."""
        redis = AsyncMock()
        redis.incr.return_value = 3
        redis.ttl.return_value = -1

        await _check_rate_limit(redis, "test:key", limit=20, window=60)

        redis.expire.assert_called_with("test:key", 60)


# ============================================================
# Integration Tests for Rate Limit Dependency
# ============================================================


class TestRateLimitDependency:
    """Tests for the rate_limit_dependency with a real FastAPI app."""

    def _create_test_app(self):
        """Create a minimal FastAPI app with rate limiting."""
        app = FastAPI()

        @app.get("/test", dependencies=[Depends(rate_limit_dependency)])
        async def test_endpoint():
            return {"status": "ok"}

        return app

    @pytest.mark.asyncio
    async def test_unauthenticated_rate_limit_allows_within_limit(self):
        """Unauthenticated requests within 20/min should succeed."""
        app = self._create_test_app()

        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 1
        mock_redis.ttl.return_value = 60

        app.dependency_overrides[
            __import__("app.core.redis", fromlist=["get_redis_cache"]).get_redis_cache
        ] = lambda: mock_redis

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")
            assert response.status_code == 200

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unauthenticated_rate_limit_blocks_over_limit(self):
        """Unauthenticated requests exceeding 20/min should get 429."""
        app = self._create_test_app()

        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 21
        mock_redis.ttl.return_value = 45

        from app.core.redis import get_redis_cache

        app.dependency_overrides[get_redis_cache] = lambda: mock_redis

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]
            assert response.headers["Retry-After"] == "45"
            assert response.headers["X-RateLimit-Limit"] == "20"
            assert response.headers["X-RateLimit-Remaining"] == "0"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_authenticated_rate_limit_uses_higher_limit(self):
        """Authenticated users should get 100 req/min limit."""
        app = self._create_test_app()

        mock_redis = AsyncMock()
        # 21 requests - would exceed unauth limit but not auth limit
        mock_redis.incr.return_value = 21
        mock_redis.ttl.return_value = 55

        from app.core.redis import get_redis_cache

        app.dependency_overrides[get_redis_cache] = lambda: mock_redis

        # Create a valid access token
        token = create_access_token(subject=str(uuid.uuid4()), role="recipient")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test",
                headers={"Authorization": f"Bearer {token}"},
            )
            # 21 < 100, so should be allowed
            assert response.status_code == 200

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_authenticated_rate_limit_blocks_over_100(self):
        """Authenticated users exceeding 100 req/min should get 429."""
        app = self._create_test_app()

        mock_redis = AsyncMock()
        mock_redis.incr.return_value = 101
        mock_redis.ttl.return_value = 30

        from app.core.redis import get_redis_cache

        app.dependency_overrides[get_redis_cache] = lambda: mock_redis

        token = create_access_token(subject=str(uuid.uuid4()), role="recipient")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 429
            assert response.headers["X-RateLimit-Limit"] == "100"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_token_treated_as_unauthenticated(self):
        """Invalid token should fallback to unauthenticated rate limit."""
        app = self._create_test_app()

        mock_redis = AsyncMock()
        # 21 requests - exceeds unauth limit
        mock_redis.incr.return_value = 21
        mock_redis.ttl.return_value = 50

        from app.core.redis import get_redis_cache

        app.dependency_overrides[get_redis_cache] = lambda: mock_redis

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/test",
                headers={"Authorization": "Bearer invalid.token.here"},
            )
            # Invalid token -> unauthenticated -> 20 limit -> 21 exceeds -> 429
            assert response.status_code == 429

        app.dependency_overrides.clear()
