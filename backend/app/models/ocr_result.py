"""OCRResult model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.compliance_submission import ComplianceSubmission


class OCRResult(Base):
    """OCR processing result with structured data extraction."""

    __tablename__ = "ocr_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("compliance_submissions.id"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("uploaded_documents.id"), nullable=False
    )
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    extraction_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    submission: Mapped["ComplianceSubmission"] = relationship(back_populates="ocr_results")
