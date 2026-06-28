"""RBAC middleware using FastAPI dependency injection.

Provides dependency functions for:
- JWT token validation (get_current_user)
- Role-based permission checks (require_roles)
- Organization-scoped access enforcement (require_org_access)
"""

import uuid
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.enums import UserRole
from app.models.user import User

settings = get_settings()

# HTTP Bearer scheme for extracting tokens from Authorization header
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT access token and return the authenticated user.

    This dependency extracts the Bearer token from the Authorization header,
    decodes and validates the JWT, then fetches the corresponding user from
    the database.

    Args:
        credentials: The HTTP Bearer credentials from the Authorization header.
        db: The async database session.

    Returns:
        The authenticated User model instance.

    Raises:
        HTTPException 401: If token is missing, expired, invalid, or user not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure this is an access token, not a refresh token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    try:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Dependency factory that checks if the current user has one of the specified roles.

    Super Admin always has unrestricted access regardless of the allowed_roles list.

    Args:
        *allowed_roles: One or more UserRole values that are permitted access.

    Returns:
        A FastAPI dependency function that validates the user's role.

    Usage:
        @router.post("/programs", dependencies=[Depends(require_roles(UserRole.ORG_ADMIN))])
        async def create_program(...): ...

        # Or inject the user directly:
        @router.get("/admin/users")
        async def list_users(user: User = Depends(require_roles(UserRole.SUPER_ADMIN))): ...
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check that the current user has one of the allowed roles.

        Super Admin always passes regardless of allowed_roles.

        Args:
            current_user: The authenticated user from get_current_user.

        Returns:
            The authenticated user if role check passes.

        Raises:
            HTTPException 403: If user does not have a permitted role.
        """
        # Super Admin has unrestricted access to all endpoints
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Required role(s): "
                + ", ".join(r.value for r in allowed_roles),
            )

        return current_user

    return role_checker


def require_org_access(org_id_param: str = "org_id") -> Callable:
    """Dependency factory that enforces organization-scoped access for Org Admins.

    Super Admins have unrestricted access to any organization's resources.
    Org Admins can only access resources belonging to their own organization.
    Recipients are denied access (they should not access org-level endpoints).

    Args:
        org_id_param: The name of the path/query parameter containing the
            organization ID. Defaults to "org_id".

    Returns:
        A FastAPI dependency function that validates organization access.

    Usage:
        @router.get("/organizations/{org_id}/programs")
        async def list_org_programs(
            org_id: uuid.UUID,
            user: User = Depends(require_org_access("org_id")),
        ): ...
    """

    from fastapi import Request

    async def org_access_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        """Validate that the user has access to the specified organization.

        Args:
            request: The FastAPI request object (for path params).
            current_user: The authenticated user.

        Returns:
            The authenticated user if access is granted.

        Raises:
            HTTPException 403: If user cannot access the specified organization.
        """
        # Super Admin has unrestricted access
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        # Recipients should not access org-scoped endpoints
        if current_user.role == UserRole.RECIPIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access organization resources",
            )

        # For Org Admins, verify organization scope
        # Get org_id from path parameters or query parameters
        target_org_id = request.path_params.get(org_id_param)
        if target_org_id is None:
            # Try query params
            target_org_id = request.query_params.get(org_id_param)

        if target_org_id is None:
            # If no org_id in the request, allow (the endpoint may filter by user's org)
            return current_user

        # Validate the org_id format and compare
        try:
            target_org_uuid = uuid.UUID(str(target_org_id))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid organization ID",
            )

        if current_user.organization_id != target_org_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: cannot access resources of another organization",
            )

        return current_user

    return org_access_checker
