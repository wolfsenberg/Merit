"""Pydantic schemas for recipient application requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import ApplicationStatus


class CreateApplicationRequest(BaseModel):
    """Schema for application submission requests.

    Validates:
    - program_id is a valid UUID
    """

    program_id: uuid.UUID = Field(..., description="The UUID of the program to apply to")


class ApplicationResponse(BaseModel):
    """Schema for application information in responses."""

    id: uuid.UUID
    recipient_id: uuid.UUID
    program_id: uuid.UUID
    status: ApplicationStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}
