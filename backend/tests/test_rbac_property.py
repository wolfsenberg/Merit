"""Property-based tests for Role-Based Access Control (Property P8).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Property P8: Role-Based Access Control
∀ request r to a protected endpoint: r.user.role ∈ endpoint.allowed_roles.
No user can access resources or perform actions outside their role's permissions:
- Recipients cannot create programs or approve verifications
- Org Admins can only manage their own organization's programs
- Super Admins have unrestricted access
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from jose import jwt

import sys
sys.path.insert(0, ".")

from app.core.config import get_settings
from app.core.security import create_access_token
from app.middleware.auth import get_current_user, require_roles, require_org_access
from app.models.enums import UserRole

app_settings = get_settings()


# ============================================================
# Strategies
# ============================================================

# Strategy for generating valid UserRole values
user_role_strategy = st.sampled_from(list(UserRole))

# Strategy for generating non-empty subsets of UserRole (endpoint allowed roles)
# Excludes SUPER_ADMIN from "allowed_roles" since the middleware logic
# always grants SUPER_ADMIN access regardless of allowed_roles list
endpoint_allowed_roles_strategy = st.lists(
    st.sampled_from([UserRole.ORG_ADMIN, UserRole.RECIPIENT]),
    min_size=1,
    max_size=2,
    unique=True,
)

# Strategy for generating UUIDs
uuid_strategy = st.builds(uuid.uuid4)

# Strategy for generating organization IDs (some users have org, some don't)
optional_org_id_strategy = st.one_of(st.none(), uuid_strategy)


def make_user_mock(
    user_id: uuid.UUID,
    role: UserRole,
    organization_id=None,
    is_active: bool = True,
):
    """Create a mock User object for testing."""
    user = MagicMock()
    user.id = user_id
    user.email = f"{role.value}_{user_id}@example.com"
    user.role = role
    user.organization_id = organization_id
    user.is_active = is_active
    user.full_name = "Test User"
    return user


# ============================================================
# Property P8: Role-Based Access Control
# ============================================================


class TestPropertyP8RoleBasedAccessControl:
    """Property P8: For all role/endpoint combinations, access is correctly granted or denied.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
    """

    @given(
        user_role=user_role_strategy,
        allowed_roles=endpoint_allowed_roles_strategy,
        user_id=uuid_strategy,
        org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_super_admin_always_has_unrestricted_access(
        self, user_role, allowed_roles, user_id, org_id
    ):
        """Requirement 2.4: Super Admin always gets unrestricted access.

        For any endpoint with any allowed_roles configuration,
        a Super Admin user should always receive 200.
        """
        # Only test with Super Admin role
        assume(user_role == UserRole.SUPER_ADMIN)

        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(require_roles(*allowed_roles))):
            return {"role": user.role.value}

        user_mock = make_user_mock(
            user_id=user_id,
            role=UserRole.SUPER_ADMIN,
            organization_id=org_id,
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.get("/protected")

        # Super Admin must ALWAYS get 200, regardless of allowed_roles
        assert response.status_code == 200, (
            f"Super Admin denied access to endpoint with allowed_roles={allowed_roles}"
        )

    @given(
        user_role=st.sampled_from([UserRole.ORG_ADMIN, UserRole.RECIPIENT]),
        allowed_roles=endpoint_allowed_roles_strategy,
        user_id=uuid_strategy,
        org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_non_super_admin_access_determined_by_allowed_roles(
        self, user_role, allowed_roles, user_id, org_id
    ):
        """Requirements 2.1, 2.6: RBAC enforced at middleware level.

        For non-Super Admin users, access is granted if and only if
        the user's role is in the endpoint's allowed_roles list.
        """
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(require_roles(*allowed_roles))):
            return {"role": user.role.value}

        user_mock = make_user_mock(
            user_id=user_id,
            role=user_role,
            organization_id=org_id,
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.get("/protected")

        if user_role in allowed_roles:
            assert response.status_code == 200, (
                f"User with role {user_role} denied access to endpoint "
                f"that allows {allowed_roles}"
            )
        else:
            assert response.status_code == 403, (
                f"User with role {user_role} granted access to endpoint "
                f"that only allows {allowed_roles}"
            )

    @given(
        user_id=uuid_strategy,
        own_org_id=uuid_strategy,
        target_org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_recipient_cannot_access_program_creation_endpoints(
        self, user_id, own_org_id, target_org_id
    ):
        """Requirement 2.2: Recipients get 403 on program creation/verification approval.

        A Recipient must never be able to access endpoints restricted to
        ORG_ADMIN (program creation, verification approval).
        """
        app = FastAPI()

        # Simulate program creation endpoint (ORG_ADMIN only)
        @app.post("/programs")
        async def create_program(user=Depends(require_roles(UserRole.ORG_ADMIN))):
            return {"created": True}

        user_mock = make_user_mock(
            user_id=user_id,
            role=UserRole.RECIPIENT,
            organization_id=None,
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.post("/programs")

        assert response.status_code == 403, (
            "Recipient was able to access program creation endpoint"
        )

    @given(
        user_id=uuid_strategy,
        own_org_id=uuid_strategy,
        target_org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_org_admin_cannot_access_different_organization(
        self, user_id, own_org_id, target_org_id
    ):
        """Requirement 2.3: Org Admins get 403 on resources from different organizations.

        An Org Admin must receive 403 when accessing resources belonging
        to a different organization than their own.
        """
        # Ensure the orgs are actually different
        assume(own_org_id != target_org_id)

        app = FastAPI()

        @app.get("/orgs/{org_id}/resources")
        async def org_resources(org_id: uuid.UUID, user=Depends(require_org_access("org_id"))):
            return {"org_id": str(org_id)}

        user_mock = make_user_mock(
            user_id=user_id,
            role=UserRole.ORG_ADMIN,
            organization_id=own_org_id,
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.get(f"/orgs/{target_org_id}/resources")

        assert response.status_code == 403, (
            f"Org Admin with org {own_org_id} accessed resources of org {target_org_id}"
        )

    @given(
        user_id=uuid_strategy,
        org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_org_admin_can_access_own_organization(self, user_id, org_id):
        """Requirement 2.3 (positive): Org Admin can access their own organization.

        An Org Admin accessing their own organization's resources should
        receive 200.
        """
        app = FastAPI()

        @app.get("/orgs/{org_id}/resources")
        async def org_resources(org_id: uuid.UUID, user=Depends(require_org_access("org_id"))):
            return {"org_id": str(org_id)}

        user_mock = make_user_mock(
            user_id=user_id,
            role=UserRole.ORG_ADMIN,
            organization_id=org_id,
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.get(f"/orgs/{org_id}/resources")

        assert response.status_code == 200, (
            f"Org Admin denied access to their own organization {org_id}"
        )

    @given(
        user_id=uuid_strategy,
        target_org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_super_admin_can_access_any_organization(self, user_id, target_org_id):
        """Requirement 2.4: Super Admin can access any organization's resources.

        Super Admin should have unrestricted access to all organization-scoped
        endpoints regardless of which org is targeted.
        """
        app = FastAPI()

        @app.get("/orgs/{org_id}/resources")
        async def org_resources(org_id: uuid.UUID, user=Depends(require_org_access("org_id"))):
            return {"org_id": str(org_id)}

        user_mock = make_user_mock(
            user_id=user_id,
            role=UserRole.SUPER_ADMIN,
            organization_id=None,  # Super Admin may not be bound to any org
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.get(f"/orgs/{target_org_id}/resources")

        assert response.status_code == 200, (
            f"Super Admin denied access to organization {target_org_id}"
        )

    @given(
        user_id=uuid_strategy,
        target_org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_recipient_cannot_access_org_scoped_endpoints(
        self, user_id, target_org_id
    ):
        """Requirement 2.2/2.3: Recipients get 403 on org-scoped endpoints.

        Recipients should be denied access to organization-scoped endpoints
        since they are not organization members with admin privileges.
        """
        app = FastAPI()

        @app.get("/orgs/{org_id}/resources")
        async def org_resources(org_id: uuid.UUID, user=Depends(require_org_access("org_id"))):
            return {"org_id": str(org_id)}

        user_mock = make_user_mock(
            user_id=user_id,
            role=UserRole.RECIPIENT,
            organization_id=None,
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.get(f"/orgs/{target_org_id}/resources")

        assert response.status_code == 403, (
            f"Recipient was able to access org-scoped endpoint for org {target_org_id}"
        )

    @given(
        user_id=uuid_strategy,
    )
    @settings(max_examples=100, deadline=None)
    def test_expired_token_returns_401(self, user_id):
        """Requirement 2.5: Expired/invalid tokens get 401.

        Any request with an expired JWT token must always receive 401 Unauthorized,
        regardless of the role encoded in the token.
        """
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        client = TestClient(app)

        # Create an expired token
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "role": "org_admin",
            "type": "access",
            "iat": now - timedelta(hours=1),
            "exp": now - timedelta(minutes=1),
            "jti": str(uuid.uuid4()),
        }
        expired_token = jwt.encode(
            payload, app_settings.jwt_secret_key, algorithm=app_settings.jwt_algorithm
        )

        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401, (
            f"Expired token for user {user_id} did not return 401"
        )

    @given(
        invalid_token=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "S"),
                                   max_codepoint=127),
            min_size=10, max_size=100,
        ).filter(lambda t: "." in t),  # Must look vaguely like JWT
    )
    @settings(max_examples=100, deadline=None)
    def test_invalid_token_returns_401(self, invalid_token):
        """Requirement 2.5: Invalid tokens get 401.

        Any request with a malformed/invalid JWT token must receive 401.
        """
        app = FastAPI()

        @app.get("/protected")
        async def protected(user=Depends(get_current_user)):
            return {"user_id": str(user.id)}

        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401, (
            f"Invalid token '{invalid_token[:20]}...' did not return 401"
        )

    @given(
        user_role=user_role_strategy,
        allowed_roles=endpoint_allowed_roles_strategy,
        user_id=uuid_strategy,
        org_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    def test_role_validated_on_every_request(
        self, user_role, allowed_roles, user_id, org_id
    ):
        """Requirement 2.6: Role validated against endpoint's allowed roles on every request.

        The role check is performed for every request (not cached).
        If the user's role is not in the allowed_roles, 403 is returned.
        If the user is SUPER_ADMIN, 200 is returned regardless.
        """
        app = FastAPI()

        @app.get("/endpoint")
        async def endpoint(user=Depends(require_roles(*allowed_roles))):
            return {"role": user.role.value}

        user_mock = make_user_mock(
            user_id=user_id,
            role=user_role,
            organization_id=org_id,
        )

        async def override_get_current_user():
            return user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        response = client.get("/endpoint")

        # Expected: Super Admin always 200, otherwise depends on role membership
        if user_role == UserRole.SUPER_ADMIN:
            assert response.status_code == 200
        elif user_role in allowed_roles:
            assert response.status_code == 200
        else:
            assert response.status_code == 403
