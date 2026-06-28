"""ComplianceSubmission model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import VerificationStatus

if TYPE_CHECKING:
    from app.models.eligibility_evaluation import EligibilityEvaluation
    from app.models.ocr_result import OCRResult
    from app.models.uploaded_document import UploadedDocument


class ComplianceSubmission(Base):
    """Compliance document submission linking recipients to program requirements."""

    __tablename__ = "compliance_submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id"), nullable=False)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_requirements.id"), nullable=False
    )
    status: Mapped[VerificationStatus] = mapped_column(
        SQLAlchemyEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    submitted_at: Mapped[datetime] = mapped_column(default=func.now())
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    documents: Mapped[list["UploadedDocument"]] = relationship(back_populates="submission")
    ocr_results: Mapped[list["OCRResult"]] = relationship(back_populates="submission")
    evaluation: Mapped[Optional["EligibilityEvaluation"]] = relationship(
        back_populates="submission"
    )
