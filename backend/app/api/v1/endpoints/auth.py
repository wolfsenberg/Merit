"""Authentication API routes.

Provides endpoints for:
- POST /register - User registration
- POST /login - User login
- POST /refresh - Token refresh
- POST /reset-password - Password reset request

Rate limiting: 20 req/min unauthenticated, 100 req/min authenticated
Implemented via Redis-based rate limiting dependency.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis_session
from app.middleware.rate_limit import rate_limit_dependency
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    AccountLockedError,
    AuthService,
    AuthServiceError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
)

router = APIRouter(dependencies=[Depends(rate_limit_dependency)])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        409: {"description": "Email already in use"},
        422: {"description": "Validation error (e.g., password too short, missing org_id for org_admin)"},
    },
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_session),
) -> UserResponse:
    """Register a new user account.

    Creates a user with the specified email, password, full name, and role.
    For org_admin role, organization_id is required.
    Password must be at least 8 characters.
    """
    service = AuthService(db=db, redis=redis)
    try:
        return await service.register(request)
    except DuplicateEmailError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    responses={
        401: {"description": "Invalid credentials"},
        423: {"description": "Account locked due to too many failed attempts"},
    },
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_session),
) -> TokenResponse:
    """Authenticate a user and return JWT tokens.

    Returns an access token (15-min expiry) and refresh token (7-day expiry).
    After 5 consecutive failed attempts, the account is locked for 30 minutes.
    """
    service = AuthService(db=db, redis=redis)
    try:
        return await service.login(request)
    except AccountLockedError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_session),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token.

    Implements token rotation: the old refresh token is invalidated
    and a new token pair is issued.
    """
    service = AuthService(db=db, redis=redis)
    try:
        return await service.refresh_token(request.refresh_token)
    except InvalidTokenError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/reset-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    responses={
        202: {"description": "Password reset request accepted (email sent if account exists)"},
    },
)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_session),
) -> dict:
    """Request a password reset.

    If the email exists, a reset token is generated and stored.
    In production, a reset email would be sent.
    Always returns 202 to avoid revealing whether the email exists.
    """
    service = AuthService(db=db, redis=redis)
    await service.reset_password(request.email)
    return {"message": "If the email is registered, a password reset link will be sent."}
