"""Authentication service with register, login, refresh, and password reset logic."""

import uuid

from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

settings = get_settings()

# Constants for account lockout
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthServiceError(Exception):
    """Base exception for auth service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DuplicateEmailError(AuthServiceError):
    """Raised when registration email is already in use."""

    def __init__(self):
        super().__init__("A user with this email already exists", status_code=409)


class InvalidCredentialsError(AuthServiceError):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__("Invalid email or password", status_code=401)


class AccountLockedError(AuthServiceError):
    """Raised when account is locked due to failed login attempts."""

    def __init__(self, minutes_remaining: int):
        super().__init__(
            f"Account is locked due to too many failed login attempts. "
            f"Try again in {minutes_remaining} minutes.",
            status_code=423,
        )


class InvalidTokenError(AuthServiceError):
    """Raised when a token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message, status_code=401)


class AuthService:
    """Service handling user authentication operations."""

    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def register(self, request: RegisterRequest) -> UserResponse:
        """Register a new user account.

        Args:
            request: Registration data with email, password, name, role.

        Returns:
            The created user response.

        Raises:
            DuplicateEmailError: If the email is already in use.
        """
        # Check for duplicate email
        existing = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateEmailError()

        # Hash password with bcrypt cost factor 12
        hashed = hash_password(request.password)

        # Create user
        user = User(
            id=uuid.uuid4(),
            email=request.email,
            password_hash=hashed,
            full_name=request.full_name,
            role=request.role,
            organization_id=request.organization_id,
            is_active=True,
            is_verified=False,
        )

        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise DuplicateEmailError()

        return UserResponse.model_validate(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate a user and return tokens.

        Args:
            request: Login data with email and password.

        Returns:
            Token response with access and refresh tokens.

        Raises:
            AccountLockedError: If the account is locked.
            InvalidCredentialsError: If credentials are invalid.
        """
        # Check account lockout
        lockout_key = f"auth:lockout:{request.email}"
        attempts_key = f"auth:failed_attempts:{request.email}"

        # Check if account is currently locked
        lockout_ttl = await self.redis.ttl(lockout_key)
        if lockout_ttl > 0:
            minutes_remaining = (lockout_ttl // 60) + 1
            raise AccountLockedError(minutes_remaining=minutes_remaining)

        # Look up user
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if user is None or not verify_password(request.password, user.password_hash):
            # Increment failed attempts
            await self._record_failed_attempt(attempts_key, lockout_key)
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AuthServiceError("Account is deactivated", status_code=403)

        # Successful login: clear failed attempts
        await self.redis.delete(attempts_key)

        # Generate tokens
        org_id = str(user.organization_id) if user.organization_id else None
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
            organization_id=org_id,
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            organization_id=org_id,
        )

        # Store refresh token in Redis for rotation tracking
        await self._store_refresh_token(str(user.id), refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a valid refresh token.

        Implements token rotation: the old refresh token is invalidated
        and a new one is issued.

        Args:
            refresh_token: The current refresh token.

        Returns:
            New token response with rotated tokens.

        Raises:
            InvalidTokenError: If the refresh token is invalid or revoked.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise InvalidTokenError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Token is not a refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Invalid token payload")

        # Verify token hasn't been revoked (rotation check)
        stored_token = await self.redis.get(f"auth:refresh_token:{user_id}")
        if stored_token != refresh_token:
            # Possible token reuse attack - invalidate all tokens for this user
            await self.redis.delete(f"auth:refresh_token:{user_id}")
            raise InvalidTokenError("Refresh token has been revoked")

        # Look up user to get current role and org
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise InvalidTokenError("User not found or deactivated")

        # Generate new token pair (rotation)
        org_id = str(user.organization_id) if user.organization_id else None
        new_access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
            organization_id=org_id,
        )
        new_refresh_token = create_refresh_token(
            subject=str(user.id),
            organization_id=org_id,
        )

        # Store new refresh token, invalidating the old one
        await self._store_refresh_token(str(user.id), new_refresh_token)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def reset_password(self, email: str) -> None:
        """Initiate a password reset request.

        In production this would send a reset email. For now,
        this validates the email exists and logs the request.

        Args:
            email: The email address to send the reset to.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            # Don't reveal whether email exists - return silently
            return

        # Generate a reset token and store it in Redis with short TTL
        reset_token = str(uuid.uuid4())
        await self.redis.set(
            f"auth:password_reset:{reset_token}",
            str(user.id),
            ex=3600,  # 1 hour expiry
        )

        # In production: send email with reset link containing token
        # For now, the token is stored and can be retrieved via admin tools

    async def _record_failed_attempt(self, attempts_key: str, lockout_key: str) -> None:
        """Record a failed login attempt, locking account after MAX_FAILED_ATTEMPTS."""
        attempts = await self.redis.incr(attempts_key)

        # Set TTL on attempts counter if it's the first attempt
        if attempts == 1:
            await self.redis.expire(attempts_key, LOCKOUT_DURATION_MINUTES * 60)

        # Lock account after MAX_FAILED_ATTEMPTS
        if attempts >= MAX_FAILED_ATTEMPTS:
            await self.redis.set(
                lockout_key,
                "locked",
                ex=LOCKOUT_DURATION_MINUTES * 60,
            )
            # Clear the attempts counter
            await self.redis.delete(attempts_key)

    async def _store_refresh_token(self, user_id: str, token: str) -> None:
        """Store a refresh token in Redis for rotation tracking."""
        await self.redis.set(
            f"auth:refresh_token:{user_id}",
            token,
            ex=settings.jwt_refresh_token_expire_days * 24 * 3600,
        )
