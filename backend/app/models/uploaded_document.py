"""UploadedDocument model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DocumentType

if TYPE_CHECKING:
    from app.models.compliance_submission import ComplianceSubmission


class UploadedDocument(Base):
    """Uploaded document with encryption metadata."""

    __tablename__ = "uploaded_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("compliance_submissions.id"), nullable=False
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SQLAlchemyEnum(DocumentType), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # Encryption metadata
    encryption_algorithm: Mapped[str] = mapped_column(String(50), default="AES-256-GCM")
    encryption_key_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    submission: Mapped["ComplianceSubmission"] = relationship(back_populates="documents")
