"""Unit tests for wallet service - Stellar wallet management and funding pools."""

import base64
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
sys.path.insert(0, ".")

from app.models.funding_pool import FundingPool
from app.models.stellar_wallet import StellarWallet
from app.schemas.wallet import (
    FundingPoolCreateRequest,
    FundingPoolResponse,
    WalletCreateRequest,
    WalletResponse,
)
from app.services.wallet_service import (
    EncryptionError,
    FundingPoolAlreadyExistsError,
    WalletAlreadyExistsError,
    WalletNotFoundError,
    WalletService,
    WalletServiceError,
    decrypt_private_key,
    encrypt_private_key,
)


# ============================================================
# Test fixtures
# ============================================================


def _generate_test_encryption_key() -> str:
    """Generate a valid 32-byte base64-encoded encryption key for tests."""
    return base64.b64encode(os.urandom(32)).decode("utf-8")


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    """Set a valid encryption key for all tests."""
    key = _generate_test_encryption_key()
    monkeypatch.setenv("WALLET_ENCRYPTION_KEY", key)


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def wallet_service(mock_db):
    """Create a WalletService instance with mocked dependencies."""
    return WalletService(db=mock_db)


# ============================================================
# Schema Validation Tests
# ============================================================


class TestWalletSchemas:
    """Tests for wallet Pydantic schemas."""

    def test_wallet_create_request_valid(self):
        """A valid wallet creation request should pass validation."""
        user_id = uuid.uuid4()
        req = WalletCreateRequest(user_id=user_id)
        assert req.user_id == user_id

    def test_funding_pool_create_request_valid(self):
        """A valid funding pool creation request should pass validation."""
        req = FundingPoolCreateRequest(
            program_id=uuid.uuid4(),
            org_id=uuid.uuid4(),
            initial_amount=5000.0,
        )
        assert req.initial_amount == 5000.0

    def test_funding_pool_create_request_rejects_zero_amount(self):
        """Funding pool initial_amount must be > 0."""
        with pytest.raises(Exception):
            FundingPoolCreateRequest(
                program_id=uuid.uuid4(),
                org_id=uuid.uuid4(),
                initial_amount=0,
            )

    def test_funding_pool_create_request_rejects_negative_amount(self):
        """Funding pool initial_amount must be positive."""
        with pytest.raises(Exception):
            FundingPoolCreateRequest(
                program_id=uuid.uuid4(),
                org_id=uuid.uuid4(),
                initial_amount=-100.0,
            )


# ============================================================
# Encryption Tests
# ============================================================


class TestEncryption:
    """Tests for private key encryption/decryption."""

    def test_encrypt_then_decrypt_roundtrip(self):
        """Encrypting and then decrypting should return the original key."""
        test_secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
        encrypted, key_id = encrypt_private_key(test_secret)
        decrypted = decrypt_private_key(encrypted, key_id)
        assert decrypted == test_secret

    def test_encryption_produces_different_outputs(self):
        """Two encryptions of the same key should produce different ciphertext (due to random nonce)."""
        test_secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
        enc1, _ = encrypt_private_key(test_secret)
        enc2, _ = encrypt_private_key(test_secret)
        assert enc1 != enc2  # Different nonces → different ciphertext

    def test_encrypt_returns_base64_string(self):
        """Encrypted output should be valid base64."""
        test_secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
        encrypted, key_id = encrypt_private_key(test_secret)
        # Should not raise
        decoded = base64.b64decode(encrypted)
        # Nonce (12 bytes) + ciphertext (>= plaintext length + 16 byte tag)
        assert len(decoded) >= 12 + len(test_secret) + 16

    def test_key_id_is_returned(self):
        """encrypt_private_key should return a key_id for rotation support."""
        test_secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
        _, key_id = encrypt_private_key(test_secret)
        assert key_id == "default-v1"

    def test_missing_encryption_key_raises_error(self, monkeypatch):
        """Missing WALLET_ENCRYPTION_KEY should raise EncryptionError."""
        monkeypatch.delenv("WALLET_ENCRYPTION_KEY", raising=False)
        with pytest.raises(EncryptionError, match="WALLET_ENCRYPTION_KEY"):
            encrypt_private_key("some_key")

    def test_invalid_encryption_key_raises_error(self, monkeypatch):
        """Invalid (wrong length) WALLET_ENCRYPTION_KEY should raise EncryptionError."""
        # Set a 16-byte key (too short for AES-256)
        short_key = base64.b64encode(os.urandom(16)).decode("utf-8")
        monkeypatch.setenv("WALLET_ENCRYPTION_KEY", short_key)
        with pytest.raises(EncryptionError, match="32 bytes"):
            encrypt_private_key("some_key")


# ============================================================
# WalletService.create_wallet Tests
# ============================================================


class TestCreateWallet:
    """Tests for WalletService.create_wallet."""

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, wallet_service, mock_db):
        """Successfully creates a wallet for a user with no existing wallet."""
        user_id = uuid.uuid4()

        # Mock: no existing wallet found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.services.wallet_service.Keypair") as MockKeypair:
            mock_kp = MagicMock()
            mock_kp.public_key = "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"
            mock_kp.secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
            MockKeypair.random.return_value = mock_kp

            result = await wallet_service.create_wallet(user_id)

        assert result.user_id == user_id
        assert result.public_key == "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"
        assert result.network == "testnet"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wallet_uniqueness_enforced(self, wallet_service, mock_db):
        """Should raise WalletAlreadyExistsError if user already has a wallet."""
        user_id = uuid.uuid4()

        # Mock: existing wallet found
        existing_wallet = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_wallet
        mock_db.execute.return_value = mock_result

        with pytest.raises(WalletAlreadyExistsError):
            await wallet_service.create_wallet(user_id)

        # Should not attempt to add or flush
        mock_db.add.assert_not_called()
        mock_db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_wallet_integrity_error_raises_already_exists(
        self, wallet_service, mock_db
    ):
        """IntegrityError during flush (race condition) should raise WalletAlreadyExistsError."""
        from sqlalchemy.exc import IntegrityError

        user_id = uuid.uuid4()

        # Mock: no existing wallet on check, but IntegrityError on flush
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.flush.side_effect = IntegrityError(
            "duplicate key", params=None, orig=Exception()
        )

        with patch("app.services.wallet_service.Keypair") as MockKeypair:
            mock_kp = MagicMock()
            mock_kp.public_key = "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"
            mock_kp.secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
            MockKeypair.random.return_value = mock_kp

            with pytest.raises(WalletAlreadyExistsError):
                await wallet_service.create_wallet(user_id)

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wallet_encrypts_private_key(self, wallet_service, mock_db):
        """The private key should be stored encrypted, not in plaintext."""
        user_id = uuid.uuid4()
        test_secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.services.wallet_service.Keypair") as MockKeypair:
            mock_kp = MagicMock()
            mock_kp.public_key = "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"
            mock_kp.secret = test_secret
            MockKeypair.random.return_value = mock_kp

            await wallet_service.create_wallet(user_id)

        # Get the wallet object that was added to the session
        added_wallet = mock_db.add.call_args[0][0]
        # The encrypted key should NOT be the plaintext secret
        assert added_wallet.encrypted_private_key != test_secret
        # It should be a base64-encoded string
        base64.b64decode(added_wallet.encrypted_private_key)
        # The key_id should be set
        assert added_wallet.encryption_key_id == "default-v1"


# ============================================================
# WalletService.get_wallet Tests
# ============================================================


class TestGetWallet:
    """Tests for WalletService.get_wallet."""

    @pytest.mark.asyncio
    async def test_get_wallet_success(self, wallet_service, mock_db):
        """Should return wallet info when wallet exists."""
        user_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        mock_wallet = MagicMock()
        mock_wallet.id = wallet_id
        mock_wallet.user_id = user_id
        mock_wallet.public_key = "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"
        mock_wallet.network = "testnet"
        mock_wallet.created_at = now

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_wallet
        mock_db.execute.return_value = mock_result

        result = await wallet_service.get_wallet(user_id)

        assert result.id == wallet_id
        assert result.user_id == user_id
        assert result.public_key == "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"

    @pytest.mark.asyncio
    async def test_get_wallet_not_found(self, wallet_service, mock_db):
        """Should raise WalletNotFoundError when no wallet exists."""
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(WalletNotFoundError):
            await wallet_service.get_wallet(user_id)


# ============================================================
# WalletService.create_funding_pool Tests
# ============================================================


class TestCreateFundingPool:
    """Tests for WalletService.create_funding_pool."""

    @pytest.mark.asyncio
    async def test_create_funding_pool_success(self, wallet_service, mock_db):
        """Successfully creates a funding pool for a program."""
        program_id = uuid.uuid4()
        org_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.services.wallet_service.Keypair") as MockKeypair:
            mock_kp = MagicMock()
            mock_kp.public_key = "GDQP2KPQGKIHYJGXNUIYOMHARUARCA7DJT5FO2FFOOBD3XCDDB5LBER"
            mock_kp.secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
            MockKeypair.random.return_value = mock_kp

            result = await wallet_service.create_funding_pool(
                program_id=program_id,
                org_id=org_id,
                initial_amount=10000.0,
            )

        assert result.program_id == program_id
        assert result.public_key == "GDQP2KPQGKIHYJGXNUIYOMHARUARCA7DJT5FO2FFOOBD3XCDDB5LBER"
        assert result.balance == 10000.0
        assert result.is_active is True
        assert result.network == "testnet"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_funding_pool_already_exists(self, wallet_service, mock_db):
        """Should raise FundingPoolAlreadyExistsError if program already has a pool."""
        program_id = uuid.uuid4()
        org_id = uuid.uuid4()

        existing_pool = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_pool
        mock_db.execute.return_value = mock_result

        with pytest.raises(FundingPoolAlreadyExistsError):
            await wallet_service.create_funding_pool(
                program_id=program_id,
                org_id=org_id,
                initial_amount=5000.0,
            )

        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_funding_pool_integrity_error(self, wallet_service, mock_db):
        """IntegrityError during flush should raise FundingPoolAlreadyExistsError."""
        from sqlalchemy.exc import IntegrityError

        program_id = uuid.uuid4()
        org_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.flush.side_effect = IntegrityError(
            "duplicate key", params=None, orig=Exception()
        )

        with patch("app.services.wallet_service.Keypair") as MockKeypair:
            mock_kp = MagicMock()
            mock_kp.public_key = "GDQP2KPQGKIHYJGXNUIYOMHARUARCA7DJT5FO2FFOOBD3XCDDB5LBER"
            mock_kp.secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"
            MockKeypair.random.return_value = mock_kp

            with pytest.raises(FundingPoolAlreadyExistsError):
                await wallet_service.create_funding_pool(
                    program_id=program_id,
                    org_id=org_id,
                    initial_amount=5000.0,
                )

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_funding_pool_encrypts_private_key(self, wallet_service, mock_db):
        """The pool's private key should be stored encrypted."""
        program_id = uuid.uuid4()
        org_id = uuid.uuid4()
        test_secret = "SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.services.wallet_service.Keypair") as MockKeypair:
            mock_kp = MagicMock()
            mock_kp.public_key = "GDQP2KPQGKIHYJGXNUIYOMHARUARCA7DJT5FO2FFOOBD3XCDDB5LBER"
            mock_kp.secret = test_secret
            MockKeypair.random.return_value = mock_kp

            await wallet_service.create_funding_pool(
                program_id=program_id,
                org_id=org_id,
                initial_amount=5000.0,
            )

        added_pool = mock_db.add.call_args[0][0]
        assert added_pool.encrypted_private_key != test_secret
        # Should be valid base64
        base64.b64decode(added_pool.encrypted_private_key)


# ============================================================
# Error Hierarchy Tests
# ============================================================


class TestErrorHierarchy:
    """Tests for error class hierarchy and properties."""

    def test_wallet_service_error_is_base(self):
        """WalletServiceError should have message and status_code."""
        err = WalletServiceError("test error", status_code=500)
        assert err.message == "test error"
        assert err.status_code == 500
        assert str(err) == "test error"

    def test_wallet_already_exists_error(self):
        """WalletAlreadyExistsError should have 409 status."""
        err = WalletAlreadyExistsError()
        assert err.status_code == 409
        assert "at most one wallet" in err.message

    def test_wallet_not_found_error(self):
        """WalletNotFoundError should have 404 status."""
        err = WalletNotFoundError()
        assert err.status_code == 404

    def test_funding_pool_already_exists_error(self):
        """FundingPoolAlreadyExistsError should have 409 status."""
        err = FundingPoolAlreadyExistsError()
        assert err.status_code == 409

    def test_encryption_error(self):
        """EncryptionError should have 500 status."""
        err = EncryptionError()
        assert err.status_code == 500
