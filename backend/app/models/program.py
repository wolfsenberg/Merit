"""Program model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, Numeric, Text, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ProgramStatus

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.funding_pool import FundingPool
    from app.models.organization import Organization
    from app.models.program_requirement import ProgramRequirement


class Program(Base):
    """Funding program with lifecycle management."""

    __tablename__ = "programs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProgramStatus] = mapped_column(
        SQLAlchemyEnum(ProgramStatus), default=ProgramStatus.DRAFT
    )
    funding_amount_per_recipient: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    max_recipients: Mapped[int] = mapped_column(Integer, nullable=False)
    current_recipients: Mapped[int] = mapped_column(Integer, default=0)
    total_funded: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    start_date: Mapped[datetime] = mapped_column(nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="programs")
    requirements: Mapped[list["ProgramRequirement"]] = relationship(back_populates="program")
    applications: Mapped[list["Application"]] = relationship(back_populates="program")
    funding_pool: Mapped[Optional["FundingPool"]] = relationship(back_populates="program")
