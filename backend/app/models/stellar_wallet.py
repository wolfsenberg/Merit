"""StellarWallet model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class StellarWallet(Base):
    """Stellar wallet with encrypted private key storage."""

    __tablename__ = "stellar_wallets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    public_key: Mapped[str] = mapped_column(String(56), unique=True, nullable=False)
    encrypted_private_key: Mapped[str] = mapped_column(String(512), nullable=False)
    encryption_key_id: Mapped[str] = mapped_column(String(255), nullable=False)
    network: Mapped[str] = mapped_column(String(20), default="testnet")
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="stellar_wallet")
