"""FundingPool model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.program import Program


class FundingPool(Base):
    """Stellar funding pool associated with a program."""

    __tablename__ = "funding_pools"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id"), unique=True, nullable=False
    )
    public_key: Mapped[str] = mapped_column(String(56), unique=True, nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(String(512), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(14, 7), default=0)
    contract_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    network: Mapped[str] = mapped_column(String(20), default="testnet")
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    program: Mapped["Program"] = relationship(back_populates="funding_pool")
