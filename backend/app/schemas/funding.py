"""Pydantic schemas for fund disbursement operations."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DisbursementRequest(BaseModel):
    """Schema for a fund disbursement request."""

    recipient_id: uuid.UUID
    program_id: uuid.UUID
    amount: float = Field(..., gt=0, description="Disbursement amount, must be positive")
    compliance_evaluation_id: uuid.UUID


class CashOutRequest(BaseModel):
    """Schema for a wallet cashout request."""

    amount: float = Field(..., gt=0, description="Cashout amount, must be positive")
    method: str
    account_number: str
    account_name: str


class CashOutResponse(BaseModel):
    """Schema for a wallet cashout response."""

    id: uuid.UUID
    user_id: uuid.UUID
    balance: float
    status: str
    memo: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DisbursementResponse(BaseModel):
    """Schema for the result of a disbursement operation."""

    id: uuid.UUID
    program_id: uuid.UUID
    recipient_id: uuid.UUID
    stellar_tx_hash: str
    from_address: str
    to_address: str
    amount: float
    asset_code: str
    status: str
    memo: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TransactionHistoryItem(BaseModel):
    """Schema for a single transaction in history."""

    id: uuid.UUID
    program_id: uuid.UUID
    recipient_id: uuid.UUID
    stellar_tx_hash: str
    from_address: str
    to_address: str
    amount: float
    asset_code: str
    status: str
    memo: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PauseDisbursementsResponse(BaseModel):
    """Schema for pause/resume disbursements response."""

    program_id: uuid.UUID
    is_active: bool
    message: str
