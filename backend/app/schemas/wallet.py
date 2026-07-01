"""Pydantic schemas for wallet and funding pool operations."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WalletCreateRequest(BaseModel):
    """Schema for wallet creation request."""

    user_id: uuid.UUID


class WalletResponse(BaseModel):
    """Schema for wallet information responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    public_key: str
    balance: float = 0.0
    network: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FundingPoolCreateRequest(BaseModel):
    """Schema for funding pool creation request."""

    program_id: uuid.UUID
    org_id: uuid.UUID
    initial_amount: float = Field(..., gt=0, description="Initial funding amount, must be positive")


class FundingPoolResponse(BaseModel):
    """Schema for funding pool responses."""

    id: uuid.UUID
    program_id: uuid.UUID
    public_key: str
    balance: float
    is_active: bool
    network: str
    created_at: datetime

    model_config = {"from_attributes": True}
