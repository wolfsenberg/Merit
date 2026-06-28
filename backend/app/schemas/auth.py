"""Pydantic schemas for authentication requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    """Schema for user registration requests.

    Validates:
    - Email is valid format
    - Password is at least 8 characters
    - organization_id is required when role is org_admin
    """

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole
    organization_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def validate_organization_for_org_admin(self) -> "RegisterRequest":
        """Ensure organization_id is provided for org_admin role."""
        if self.role == UserRole.ORG_ADMIN and self.organization_id is None:
            raise ValueError("organization_id is required for org_admin role")
        return self


class LoginRequest(BaseModel):
    """Schema for user login requests."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for authentication token responses."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh requests."""

    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user information in responses."""

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    organization_id: Optional[uuid.UUID] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ResetPasswordRequest(BaseModel):
    """Schema for password reset requests."""

    email: EmailStr
