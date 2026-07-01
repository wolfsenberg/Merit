"""ProgramRequirement model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RequirementType

if TYPE_CHECKING:
    from app.models.program import Program


class ProgramRequirement(Base):
    """Configurable requirement for a funding program."""

    __tablename__ = "program_requirements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id"), nullable=False)
    requirement_type: Mapped[RequirementType] = mapped_column(
        SQLAlchemyEnum(RequirementType), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    condition_operator: Mapped[str] = mapped_column(String(20), nullable=False)
    condition_value: Mapped[str] = mapped_column(String(255), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(default=True)
    verification_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    program: Mapped["Program"] = relationship(back_populates="requirements")
