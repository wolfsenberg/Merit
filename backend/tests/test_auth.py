"""Unit tests for authentication module - security utilities and schemas."""

import sys
import uuid

import pytest
from jose import jwt

sys.path.insert(0, ".")

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest

settings = get_settings()


# ============================================================
# Password Hashing Tests
# ============================================================


class TestPasswordHashing:
    """Tests for bcrypt password hashing with cost factor 12."""

    def test_hash_password_returns_bcrypt_hash(self):
        """Hashed password should be a valid bcrypt hash."""
        hashed = hash_password("securepassword123")
        # bcrypt hashes start with $2b$ (or $2a$/$2y$)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_hash_password_uses_cost_factor_12(self):
        """Hashed password should use bcrypt cost factor 12."""
        hashed = hash_password("testpassword")
        # bcrypt format: $2b$12$...
        parts = hashed.split("$")
        assert parts[2] == "12"

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "my_secure_pass!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Wrong password should fail verification."""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_produces_different_hashes_for_same_input(self):
        """Same password should produce different hashes (due to salt)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


# ============================================================
# JWT Token Tests
# ============================================================


class TestJWTTokens:
    """Tests for JWT access and refresh token generation."""

    def test_create_access_token_contains_required_claims(self):
        """Access token should contain sub, role, type, exp, iat, jti."""
        user_id = str(uuid.uuid4())
        token = create_access_token(subject=user_id, role="recipient")
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        assert payload["sub"] == user_id
        assert payload["role"] == "recipient"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_access_token_expires_in_15_minutes(self):
        """Access token should expire approximately 15 minutes from creation."""
        token = create_access_token(subject="user123", role="recipient")
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        iat = payload["iat"]
        exp = payload["exp"]
        diff = exp - iat
        # Should be 15 minutes (900 seconds)
        assert diff == settings.jwt_access_token_expire_minutes * 60

    def test_access_token_includes_organization_id(self):
        """Access token should include org_id claim when provided."""
        org_id = str(uuid.uuid4())
        token = create_access_token(subject="user1", role="org_admin", organization_id=org_id)
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        assert payload["org_id"] == org_id

    def test_access_token_without_organization_id(self):
        """Access token should not include org_id when not provided."""
        token = create_access_token(subject="user1", role="recipient")
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        assert "org_id" not in payload

    def test_create_refresh_token_has_correct_type(self):
        """Refresh token should have type='refresh'."""
        token = create_refresh_token(subject="user123")
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        assert payload["type"] == "refresh"
        assert payload["sub"] == "user123"

    def test_refresh_token_expires_in_7_days(self):
        """Refresh token should expire in 7 days."""
        token = create_refresh_token(subject="user123")
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        iat = payload["iat"]
        exp = payload["exp"]
        diff = exp - iat
        # Should be 7 days in seconds
        assert diff == settings.jwt_refresh_token_expire_days * 24 * 3600

    def test_decode_token_valid(self):
        """Valid token should decode successfully."""
        token = create_access_token(subject="user1", role="recipient")
        payload = decode_token(token)

        assert payload["sub"] == "user1"
        assert payload["role"] == "recipient"

    def test_decode_token_invalid(self):
        """Invalid token should raise JWTError."""
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_each_token_has_unique_jti(self):
        """Each token should have a unique JTI (JWT ID)."""
        token1 = create_access_token(subject="user1", role="recipient")
        token2 = create_access_token(subject="user1", role="recipient")

        payload1 = decode_token(token1)
        payload2 = decode_token(token2)

        assert payload1["jti"] != payload2["jti"]


# ============================================================
# Schema Validation Tests
# ============================================================


class TestRegisterRequestSchema:
    """Tests for RegisterRequest Pydantic schema validation."""

    def test_valid_registration(self):
        """Valid registration data should pass validation."""
        req = RegisterRequest(
            email="test@example.com",
            password="securepass123",
            full_name="Test User",
            role=UserRole.RECIPIENT,
        )
        assert req.email == "test@example.com"
        assert req.full_name == "Test User"
        assert req.role == UserRole.RECIPIENT

    def test_password_minimum_8_chars(self):
        """Password shorter than 8 characters should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com",
                password="short",
                full_name="Test User",
                role=UserRole.RECIPIENT,
            )
        errors = exc_info.value.errors()
        assert any("password" in str(e["loc"]) for e in errors)

    def test_password_exactly_8_chars_accepted(self):
        """Password with exactly 8 characters should be accepted."""
        req = RegisterRequest(
            email="test@example.com",
            password="12345678",
            full_name="Test User",
            role=UserRole.RECIPIENT,
        )
        assert len(req.password) == 8

    def test_invalid_email_rejected(self):
        """Invalid email format should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegisterRequest(
                email="not-an-email",
                password="securepass123",
                full_name="Test User",
                role=UserRole.RECIPIENT,
            )

    def test_org_admin_requires_organization_id(self):
        """Org admin role without organization_id should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="admin@org.com",
                password="securepass123",
                full_name="Org Admin",
                role=UserRole.ORG_ADMIN,
            )
        assert "organization_id" in str(exc_info.value)

    def test_org_admin_with_organization_id_accepted(self):
        """Org admin with organization_id should pass validation."""
        org_id = uuid.uuid4()
        req = RegisterRequest(
            email="admin@org.com",
            password="securepass123",
            full_name="Org Admin",
            role=UserRole.ORG_ADMIN,
            organization_id=org_id,
        )
        assert req.organization_id == org_id

    def test_recipient_without_organization_id_accepted(self):
        """Recipient role without organization_id should pass."""
        req = RegisterRequest(
            email="recipient@example.com",
            password="securepass123",
            full_name="Recipient User",
            role=UserRole.RECIPIENT,
        )
        assert req.organization_id is None

    def test_empty_full_name_rejected(self):
        """Empty full name should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com",
                password="securepass123",
                full_name="",
                role=UserRole.RECIPIENT,
            )


class TestLoginRequestSchema:
    """Tests for LoginRequest Pydantic schema validation."""

    def test_valid_login(self):
        """Valid login data should pass validation."""
        req = LoginRequest(email="test@example.com", password="mypassword")
        assert req.email == "test@example.com"
        assert req.password == "mypassword"

    def test_invalid_email_rejected(self):
        """Invalid email in login should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LoginRequest(email="invalid", password="mypassword")
