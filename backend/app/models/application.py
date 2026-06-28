"""Application model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.program import Program
    from app.models.user import User


class Application(Base):
    """Recipient application to a funding program."""

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id"), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLAlchemyEnum(ApplicationStatus), default=ApplicationStatus.PENDING
    )
    submitted_at: Mapped[datetime] = mapped_column(default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    recipient: Mapped["User"] = relationship(foreign_keys=[recipient_id])
    program: Mapped["Program"] = relationship(back_populates="applications")
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])
