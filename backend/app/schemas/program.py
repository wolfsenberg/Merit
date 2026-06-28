"""Pydantic schemas for program management requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ProgramStatus, RequirementType


class CreateProgramRequest(BaseModel):
    """Schema for program creation requests.

    Validates:
    - funding_amount_per_recipient > 0
    - max_recipients >= 1
    - end_date > start_date (when end_date is provided)
    """

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    funding_amount_per_recipient: float = Field(..., gt=0)
    max_recipients: int = Field(..., ge=1)
    start_date: datetime
    end_date: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateProgramRequest":
        """Ensure end_date is after start_date when provided."""
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class UpdateProgramRequest(BaseModel):
    """Schema for updating program fields (only DRAFT programs can be updated)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    funding_amount_per_recipient: Optional[float] = Field(None, gt=0)
    max_recipients: Optional[int] = Field(None, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProgramResponse(BaseModel):
    """Schema for program information in responses."""

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str
    status: ProgramStatus
    funding_amount_per_recipient: float
    max_recipients: int
    current_recipients: int
    total_funded: float
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgramListResponse(BaseModel):
    """Schema for paginated program list response using cursor-based pagination."""

    items: list[ProgramResponse]
    next_cursor: Optional[str] = None
    has_more: bool


# Valid condition operators for requirement evaluation
VALID_CONDITION_OPERATORS = frozenset(
    {"lte", "gte", "eq", "neq", "lt", "gt", "contains", "exists", "not_exists"}
)

# Valid verification frequencies
VALID_VERIFICATION_FREQUENCIES = frozenset(
    {"once", "per_semester", "monthly", "quarterly", "annually"}
)


class AddRequirementRequest(BaseModel):
    """Schema for adding a requirement to a program.

    Validates:
    - requirement_type is a valid RequirementType enum value
    - condition_operator is one of: lte, gte, eq, neq, lt, gt, contains, exists, not_exists
    - verification_frequency is one of: once, per_semester, monthly, quarterly, annually
    """

    requirement_type: RequirementType
    description: str = Field(..., min_length=1, max_length=500)
    condition_operator: str = Field(..., min_length=1)
    condition_value: str = Field(..., max_length=255)
    is_mandatory: bool = True
    verification_frequency: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_fields(self) -> "AddRequirementRequest":
        """Validate condition_operator and verification_frequency values."""
        if self.condition_operator not in VALID_CONDITION_OPERATORS:
            raise ValueError(
                f"Invalid condition_operator '{self.condition_operator}'. "
                f"Must be one of: {', '.join(sorted(VALID_CONDITION_OPERATORS))}"
            )
        if self.verification_frequency not in VALID_VERIFICATION_FREQUENCIES:
            raise ValueError(
                f"Invalid verification_frequency '{self.verification_frequency}'. "
                f"Must be one of: {', '.join(sorted(VALID_VERIFICATION_FREQUENCIES))}"
            )
        return self


class RequirementResponse(BaseModel):
    """Schema for requirement information in responses."""

    id: uuid.UUID
    program_id: uuid.UUID
    requirement_type: RequirementType
    description: str
    condition_operator: str
    condition_value: str
    is_mandatory: bool
    verification_frequency: str
    created_at: datetime

    model_config = {"from_attributes": True}
