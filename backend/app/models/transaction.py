"""Transaction model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Transaction(Base):
    """Stellar transaction record with unique tx hash."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id"), nullable=False)
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    stellar_tx_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    from_address: Mapped[str] = mapped_column(String(56), nullable=False)
    to_address: Mapped[str] = mapped_column(String(56), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 7), nullable=False)
    asset_code: Mapped[str] = mapped_column(String(12), default="XLM")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    memo: Mapped[Optional[str]] = mapped_column(String(28), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
