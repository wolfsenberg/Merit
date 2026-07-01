"""Password hashing and JWT token utilities."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import jwt

from app.core.config import get_settings

settings = get_settings()

# Bcrypt cost factor (work factor / rounds)
BCRYPT_COST_FACTOR = 12


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12.

    Args:
        password: The plain text password to hash.

    Returns:
        The bcrypt hashed password string.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The bcrypt hashed password to check against.

    Returns:
        True if the password matches, False otherwise.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(
    subject: str,
    role: str,
    organization_id: Optional[str] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create a JWT access token with 15-minute expiry.

    Args:
        subject: The user ID (sub claim).
        role: The user's role.
        organization_id: Optional organization ID for org-scoped users.
        extra_claims: Optional additional claims to include.

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }

    if organization_id:
        payload["org_id"] = organization_id

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    organization_id: Optional[str] = None,
) -> str:
    """Create a JWT refresh token with 7-day expiry.

    Args:
        subject: The user ID (sub claim).
        organization_id: Optional organization ID.

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }

    if organization_id:
        payload["org_id"] = organization_id

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string.

    Returns:
        The decoded token payload.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
