"""Stellar wallet management service.

Handles keypair generation, encrypted storage, wallet uniqueness enforcement,
and funding pool account creation on the Stellar network.
"""

import base64
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from stellar_sdk import Keypair

from app.core.config import get_settings
from app.models.funding_pool import FundingPool
from app.models.stellar_wallet import StellarWallet
from app.schemas.wallet import FundingPoolResponse, WalletResponse

settings = get_settings()


class WalletServiceError(Exception):
    """Base exception for wallet service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class WalletAlreadyExistsError(WalletServiceError):
    """Raised when a user already has a wallet."""

    def __init__(self):
        super().__init__(
            "User already has a Stellar wallet. Each user can have at most one wallet.",
            status_code=409,
        )


class WalletNotFoundError(WalletServiceError):
    """Raised when a wallet is not found for the user."""

    def __init__(self):
        super().__init__("No wallet found for this user.", status_code=404)


class FundingPoolAlreadyExistsError(WalletServiceError):
    """Raised when a funding pool already exists for the program."""

    def __init__(self):
        super().__init__(
            "A funding pool already exists for this program.",
            status_code=409,
        )


class EncryptionError(WalletServiceError):
    """Raised when encryption/decryption of keys fails."""

    def __init__(self, message: str = "Failed to encrypt/decrypt key material."):
        super().__init__(message, status_code=500)


def _get_encryption_key() -> bytes:
    """Retrieve the AES-256-GCM encryption key from environment.

    The key must be a 32-byte value, base64-encoded, stored in the
    WALLET_ENCRYPTION_KEY environment variable. Never hardcode this value.

    Returns:
        The raw 32-byte encryption key.

    Raises:
        EncryptionError: If the key is missing or invalid.
    """
    key_b64 = os.environ.get("WALLET_ENCRYPTION_KEY")
    if not key_b64:
        raise EncryptionError(
            "WALLET_ENCRYPTION_KEY environment variable is not set. "
            "Cannot encrypt wallet private keys."
        )
    try:
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise EncryptionError(
                "WALLET_ENCRYPTION_KEY must be exactly 32 bytes (base64-encoded)."
            )
        return key
    except Exception as e:
        if isinstance(e, EncryptionError):
            raise
        raise EncryptionError(f"Invalid WALLET_ENCRYPTION_KEY: {e}")


def encrypt_private_key(private_key: str) -> tuple[str, str]:
    """Encrypt a Stellar private key using AES-256-GCM.

    Args:
        private_key: The Stellar secret seed (S...) to encrypt.

    Returns:
        A tuple of (encrypted_data_b64, key_id) where encrypted_data_b64
        contains the nonce prepended to the ciphertext, base64-encoded.
    """
    encryption_key = _get_encryption_key()
    aesgcm = AESGCM(encryption_key)

    # Generate a 12-byte random nonce
    nonce = os.urandom(12)

    # Encrypt the private key
    ciphertext = aesgcm.encrypt(nonce, private_key.encode("utf-8"), None)

    # Prepend nonce to ciphertext and base64-encode
    encrypted_data = base64.b64encode(nonce + ciphertext).decode("utf-8")

    # Key ID identifies which encryption key was used (allows key rotation)
    key_id = "default-v1"

    return encrypted_data, key_id


def decrypt_private_key(encrypted_data_b64: str, key_id: str) -> str:
    """Decrypt an encrypted Stellar private key.

    Args:
        encrypted_data_b64: Base64-encoded nonce + ciphertext.
        key_id: Identifier for the encryption key used.

    Returns:
        The decrypted Stellar secret seed.
    """
    encryption_key = _get_encryption_key()
    aesgcm = AESGCM(encryption_key)

    raw = base64.b64decode(encrypted_data_b64)
    nonce = raw[:12]
    ciphertext = raw[12:]

    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


class WalletService:
    """Service for managing Stellar wallets and funding pools."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_wallet(self, user_id: uuid.UUID) -> WalletResponse:
        """Generate a Stellar keypair and create a wallet record for a user.

        Enforces wallet uniqueness: each user may have at most one wallet.

        Args:
            user_id: The UUID of the user to create a wallet for.

        Returns:
            WalletResponse with the new wallet's public information.

        Raises:
            WalletAlreadyExistsError: If the user already has a wallet.
        """
        # Check if user already has a wallet (enforce uniqueness)
        existing = await self.db.execute(
            select(StellarWallet).where(StellarWallet.user_id == user_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise WalletAlreadyExistsError()

        # Generate Stellar keypair
        keypair = Keypair.random()
        public_key = keypair.public_key
        secret_key = keypair.secret

        # Encrypt private key (never store plaintext)
        encrypted_secret, key_id = encrypt_private_key(secret_key)

        # Determine network from settings
        network = getattr(settings, "stellar_network", "testnet")

        # Create wallet record
        wallet = StellarWallet(
            id=uuid.uuid4(),
            user_id=user_id,
            public_key=public_key,
            encrypted_private_key=encrypted_secret,
            encryption_key_id=key_id,
            network=network,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(wallet)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise WalletAlreadyExistsError()

        return WalletResponse.model_validate(wallet)

    async def get_wallet(self, user_id: uuid.UUID) -> WalletResponse:
        """Get wallet information for a user.

        Args:
            user_id: The UUID of the user.

        Returns:
            WalletResponse with the wallet's public information.

        Raises:
            WalletNotFoundError: If the user has no wallet.
        """
        result = await self.db.execute(
            select(StellarWallet).where(StellarWallet.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()
        if wallet is None:
            raise WalletNotFoundError()

        return WalletResponse.model_validate(wallet)

    async def create_funding_pool(
        self,
        program_id: uuid.UUID,
        org_id: uuid.UUID,
        initial_amount: float,
    ) -> FundingPoolResponse:
        """Create a funding pool account on the Stellar network for a program.

        Generates a new Stellar keypair for the pool, encrypts the private key,
        and stores the pool record.

        Args:
            program_id: The UUID of the program to fund.
            org_id: The UUID of the organization funding the program.
            initial_amount: The initial balance to assign to the pool.

        Returns:
            FundingPoolResponse with the new pool's information.

        Raises:
            FundingPoolAlreadyExistsError: If the program already has a pool.
        """
        # Check if program already has a funding pool
        existing = await self.db.execute(
            select(FundingPool).where(FundingPool.program_id == program_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise FundingPoolAlreadyExistsError()

        # Generate Stellar keypair for the funding pool
        keypair = Keypair.random()
        public_key = keypair.public_key
        secret_key = keypair.secret

        # Encrypt private key
        encrypted_secret, key_id = encrypt_private_key(secret_key)

        # Determine network from settings
        network = getattr(settings, "stellar_network", "testnet")

        # Create funding pool record
        pool = FundingPool(
            id=uuid.uuid4(),
            program_id=program_id,
            public_key=public_key,
            encrypted_private_key=encrypted_secret,
            balance=initial_amount,
            is_active=True,
            network=network,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(pool)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise FundingPoolAlreadyExistsError()

        return FundingPoolResponse.model_validate(pool)
