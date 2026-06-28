"""EligibilityEvaluation model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EligibilityStatus

if TYPE_CHECKING:
    from app.models.compliance_submission import ComplianceSubmission


class EligibilityEvaluation(Base):
    """Eligibility evaluation result with rule-by-rule outcomes."""

    __tablename__ = "eligibility_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("compliance_submissions.id"), nullable=False
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id"), nullable=False)
    overall_status: Mapped[EligibilityStatus] = mapped_column(
        SQLAlchemyEnum(EligibilityStatus), nullable=False
    )
    rule_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(default=func.now())
    next_evaluation_due: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    submission: Mapped["ComplianceSubmission"] = relationship(back_populates="evaluation")
