"""Pydantic schemas for document upload requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import DocumentType, VerificationStatus


class DocumentResponse(BaseModel):
    """Schema for document information in responses."""

    id: uuid.UUID
    submission_id: uuid.UUID
    document_type: DocumentType
    original_filename: str
    storage_path: str
    file_size_bytes: int
    mime_type: str
    encryption_algorithm: str
    encryption_key_id: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class UploadDocumentResponse(BaseModel):
    """Schema for document upload response."""

    id: uuid.UUID
    submission_id: uuid.UUID
    document_type: DocumentType
    original_filename: str
    file_size_bytes: int
    mime_type: str
    status: VerificationStatus = VerificationStatus.PENDING
    uploaded_at: datetime

    model_config = {"from_attributes": True}
