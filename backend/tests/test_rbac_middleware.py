"""Unit tests for RBAC middleware - JWT validation and role-based access control."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from jose import jwt

import sys
sys.path.insert(0, ".")

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.middleware.auth import get_current_user, require_roles, require_org_access
from app.models.enums import UserRole

settings = get_settings()


# ============================================================
# Helpers
# ============================================================


def make_user_mock(
    user_id: uuid.UUID = None,
    role: UserRole = UserRole.RECIPIENT,
    organization_id: uuid.UUID = None,
    is_active: bool = True,
):
    """Create a mock User object."""
    if user_id is None:
        user_id = uuid.uuid4()
    user = MagicMock()
    user.id = user_id
    user.email = f"{role.value}@example.com"
    user.role = role
    user.organization_id = organization_id
    user.is_active = is_active
    user.full_name = "Test User"
    return user


def make_expired_token(subject: str, role: str = "recipient") -> str:
    """Create a JWT token that is already expired."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now - timedelta(hours=1),
        "exp": now - timedelta(minutes=1),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# ============================================================
# get_current_user Tests
# ============================================================


class TestGetCurrentUser:
    """Tests for the get_current_user dependency."""

    def test_missing_token_returns_401(self):
        """Request without Authorization header should return 401."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        client = TestClient(app)
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]

    def test_invalid_token_returns_401(self):
        """Request with invalid JWT should return 401."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    def test_expired_token_returns_401(self):
        """Request with expired JWT should return 401."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        client = TestClient(app)
        expired_token = make_expired_token(str(uuid.uuid4()))
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    def test_refresh_token_rejected_as_access_token(self):
        """Refresh token should not be accepted for accessing protected endpoints."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        client = TestClient(app)
        refresh_token = create_refresh_token(subject=str(uuid.uuid4()))
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]

    def test_valid_token_with_active_user_succeeds(self):
        """Valid access token with an active user should succeed."""
        user_id = uuid.uuid4()
        org_id = uuid.uuid4()
        user_mock = make_user_mock(user_id=user_id, role=UserRole.ORG_ADMIN, organization_id=org_id)

        # Mock the database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user_mock
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def override_get_db():
            yield mock_session

        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id), "role": user.role.value}

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        token = create_access_token(
            subject=str(user_id), role=UserRole.ORG_ADMIN.value, organization_id=str(org_id)
        )
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["user_id"] == str(user_id)

    def test_valid_token_with_inactive_user_returns_401(self):
        """Valid token for a deactivated user should return 401."""
        user_id = uuid.uuid4()
        user_mock = make_user_mock(user_id=user_id, is_active=False)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user_mock
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def override_get_db():
            yield mock_session

        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        token = create_access_token(subject=str(user_id), role=UserRole.RECIPIENT.value)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert "deactivated" in response.json()["detail"]

    def test_valid_token_user_not_found_returns_401(self):
        """Valid token for a deleted/nonexistent user should return 401."""
        user_id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def override_get_db():
            yield mock_session

        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        token = create_access_token(subject=str(user_id), role=UserRole.RECIPIENT.value)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]


# ============================================================
# require_roles Tests
# ============================================================


class TestRequireRoles:
    """Tests for the require_roles dependency factory."""

    def _create_app_with_role_check(self, *allowed_roles):
        """Helper to create a FastAPI app with role-protected endpoint."""
        app = FastAPI()

        @app.get("/role-protected")
        async def role_protected(user=Depends(require_roles(*allowed_roles))):
            return {"role": user.role.value}

        return app

    def _override_current_user(self, app, user_mock):
        """Override get_current_user dependency with a mock user."""
        async def override():
            return user_mock

        app.dependency_overrides[get_current_user] = override

    def test_super_admin_always_allowed(self):
        """Super Admin should have unrestricted access to any endpoint."""
        app = self._create_app_with_role_check(UserRole.ORG_ADMIN)
        user = make_user_mock(role=UserRole.SUPER_ADMIN)
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get("/role-protected")
        assert response.status_code == 200
        assert response.json()["role"] == "super_admin"

    def test_allowed_role_succeeds(self):
        """User with an allowed role should access the endpoint."""
        app = self._create_app_with_role_check(UserRole.ORG_ADMIN, UserRole.RECIPIENT)
        user = make_user_mock(role=UserRole.ORG_ADMIN, organization_id=uuid.uuid4())
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get("/role-protected")
        assert response.status_code == 200
        assert response.json()["role"] == "org_admin"

    def test_disallowed_role_returns_403(self):
        """User without the required role should get 403."""
        app = self._create_app_with_role_check(UserRole.ORG_ADMIN)
        user = make_user_mock(role=UserRole.RECIPIENT)
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get("/role-protected")
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_recipient_cannot_access_admin_endpoint(self):
        """Recipient should not access Super Admin endpoints (403)."""
        app = self._create_app_with_role_check(UserRole.SUPER_ADMIN)
        user = make_user_mock(role=UserRole.RECIPIENT)
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get("/role-protected")
        assert response.status_code == 403

    def test_org_admin_cannot_access_super_admin_only(self):
        """Org Admin should not access Super Admin only endpoints (403)."""
        app = self._create_app_with_role_check(UserRole.SUPER_ADMIN)
        user = make_user_mock(role=UserRole.ORG_ADMIN, organization_id=uuid.uuid4())
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get("/role-protected")
        assert response.status_code == 403

    def test_multiple_allowed_roles(self):
        """Endpoint allowing multiple roles should accept any of them."""
        app = self._create_app_with_role_check(UserRole.ORG_ADMIN, UserRole.RECIPIENT)
        user = make_user_mock(role=UserRole.RECIPIENT)
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get("/role-protected")
        assert response.status_code == 200
        assert response.json()["role"] == "recipient"


# ============================================================
# require_org_access Tests
# ============================================================


class TestRequireOrgAccess:
    """Tests for the require_org_access dependency factory."""

    def _create_app_with_org_check(self):
        """Helper to create a FastAPI app with org-scoped endpoint."""
        app = FastAPI()

        @app.get("/orgs/{org_id}/resources")
        async def org_resources(org_id: uuid.UUID, user=Depends(require_org_access("org_id"))):
            return {"org_id": str(org_id), "user_role": user.role.value}

        return app

    def _override_current_user(self, app, user_mock):
        """Override get_current_user dependency."""
        async def override():
            return user_mock

        app.dependency_overrides[get_current_user] = override

    def test_super_admin_can_access_any_org(self):
        """Super Admin should access any organization's resources."""
        app = self._create_app_with_org_check()
        user = make_user_mock(role=UserRole.SUPER_ADMIN)
        self._override_current_user(app, user)

        target_org = uuid.uuid4()
        client = TestClient(app)
        response = client.get(f"/orgs/{target_org}/resources")
        assert response.status_code == 200
        assert response.json()["org_id"] == str(target_org)

    def test_org_admin_can_access_own_org(self):
        """Org Admin should access their own organization's resources."""
        org_id = uuid.uuid4()
        app = self._create_app_with_org_check()
        user = make_user_mock(role=UserRole.ORG_ADMIN, organization_id=org_id)
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get(f"/orgs/{org_id}/resources")
        assert response.status_code == 200
        assert response.json()["org_id"] == str(org_id)

    def test_org_admin_cannot_access_other_org(self):
        """Org Admin should NOT access another organization's resources (403)."""
        own_org = uuid.uuid4()
        other_org = uuid.uuid4()
        app = self._create_app_with_org_check()
        user = make_user_mock(role=UserRole.ORG_ADMIN, organization_id=own_org)
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get(f"/orgs/{other_org}/resources")
        assert response.status_code == 403
        assert "another organization" in response.json()["detail"]

    def test_recipient_cannot_access_org_resources(self):
        """Recipient should NOT access org-scoped endpoints (403)."""
        org_id = uuid.uuid4()
        app = self._create_app_with_org_check()
        user = make_user_mock(role=UserRole.RECIPIENT)
        self._override_current_user(app, user)

        client = TestClient(app)
        response = client.get(f"/orgs/{org_id}/resources")
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
