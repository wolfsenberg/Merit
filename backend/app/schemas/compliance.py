"""Pydantic schemas for compliance evaluation requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import EligibilityStatus


class RuleResultResponse(BaseModel):
    """Schema for a single rule evaluation result."""

    requirement_id: str
    requirement_type: str
    condition: str
    actual_value: Optional[str] = None
    expected_value: str
    passed: bool
    is_mandatory: bool
    reason: str


class EligibilityEvaluationResponse(BaseModel):
    """Schema for an eligibility evaluation response."""

    id: uuid.UUID
    submission_id: Optional[uuid.UUID] = None
    recipient_id: uuid.UUID
    program_id: uuid.UUID
    overall_status: EligibilityStatus
    rule_results: Optional[list[RuleResultResponse]] = None
    evaluated_at: datetime
    next_evaluation_due: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvaluateEligibilityRequest(BaseModel):
    """Schema for triggering an eligibility evaluation."""

    recipient_id: uuid.UUID
    program_id: uuid.UUID


class BatchEvaluationRequest(BaseModel):
    """Schema for triggering batch evaluation of all recipients in a program."""

    program_id: uuid.UUID


class BatchEvaluationResponse(BaseModel):
    """Schema for batch evaluation results."""

    program_id: uuid.UUID
    total_evaluated: int
    results: list[EligibilityEvaluationResponse]
    evaluated_at: datetime
