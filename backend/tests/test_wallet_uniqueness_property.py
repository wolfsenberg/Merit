"""Property-based tests for Wallet Uniqueness (Property P9).

**Validates: Requirements 8.2**

Property P9: Wallet Uniqueness
∀ user u: There exists at most one StellarWallet w where w.user_id == u.id.
Each user has exactly zero or one wallet, and wallet public keys are globally unique.
"""

import base64
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

import sys
sys.path.insert(0, ".")

from app.services.wallet_service import (
    WalletAlreadyExistsError,
    WalletService,
)


# ============================================================
# Strategies
# ============================================================

# Strategy for generating user UUIDs
uuid_strategy = st.builds(uuid.uuid4)

# Strategy for generating lists of distinct user UUIDs
distinct_user_ids_strategy = st.lists(
    uuid_strategy,
    min_size=2,
    max_size=10,
    unique_by=lambda x: str(x),
)


# ============================================================
# Helpers
# ============================================================


def _generate_test_encryption_key() -> str:
    """Generate a valid 32-byte base64-encoded encryption key for tests."""
    return base64.b64encode(os.urandom(32)).decode("utf-8")


def _make_mock_db_with_existing_wallet():
    """Create a mock DB that simulates an existing wallet found on query."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()

    existing_wallet = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_wallet
    db.execute.return_value = mock_result

    return db


def _make_mock_db_no_wallet():
    """Create a mock DB that simulates no existing wallet (first call succeeds)."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    return db


def _make_mock_db_first_succeeds_then_exists():
    """Create a mock DB that returns None on first execute (no wallet),
    then returns an existing wallet on subsequent executes."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()

    # First call: no wallet exists; subsequent calls: wallet exists
    no_wallet_result = MagicMock()
    no_wallet_result.scalar_one_or_none.return_value = None

    existing_wallet_result = MagicMock()
    existing_wallet_result.scalar_one_or_none.return_value = MagicMock()

    db.execute.side_effect = [no_wallet_result, existing_wallet_result]

    return db


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    """Set a valid encryption key for all tests."""
    key = _generate_test_encryption_key()
    monkeypatch.setenv("WALLET_ENCRYPTION_KEY", key)


# ============================================================
# Property 1: One wallet per user - duplicate creation raises error
# ============================================================


class TestPropertyP9WalletUniqueness:
    """Property P9: Each user has at most one StellarWallet;
    wallet public keys are globally unique.

    **Validates: Requirements 8.2**
    """

    @given(user_id=uuid_strategy)
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_duplicate_wallet_creation_always_raises_error(self, user_id: uuid.UUID):
        """For any user_id, calling create_wallet when a wallet already exists
        should always raise WalletAlreadyExistsError.

        **Validates: Requirements 8.2**
        """
        # Simulate a DB where the user already has a wallet
        mock_db = _make_mock_db_with_existing_wallet()
        service = WalletService(db=mock_db)

        with pytest.raises(WalletAlreadyExistsError):
            await service.create_wallet(user_id)

        # Should not attempt to add or flush (no wallet creation attempted)
        mock_db.add.assert_not_called()
        mock_db.flush.assert_not_called()

    @given(user_id=uuid_strategy)
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_second_create_wallet_call_always_raises_error(self, user_id: uuid.UUID):
        """For any user_id, calling create_wallet twice should always raise
        WalletAlreadyExistsError the second time.

        First call succeeds (no existing wallet), second call fails (wallet exists).

        **Validates: Requirements 8.2**
        """
        mock_db = _make_mock_db_first_succeeds_then_exists()
        service = WalletService(db=mock_db)

        with patch("app.services.wallet_service.Keypair") as MockKeypair:
            mock_kp = MagicMock()
            mock_kp.public_key = f"G{'A' * 55}"  # Valid-length Stellar public key
            mock_kp.secret = f"S{'B' * 55}"  # Valid-length Stellar secret key
            MockKeypair.random.return_value = mock_kp

            # First call should succeed
            result = await service.create_wallet(user_id)
            assert result is not None

            # Second call should raise WalletAlreadyExistsError
            with pytest.raises(WalletAlreadyExistsError):
                await service.create_wallet(user_id)

    @given(user_ids=distinct_user_ids_strategy)
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_distinct_users_get_unique_public_keys(self, user_ids: list):
        """For any set of distinct user_ids, each generated wallet has a
        unique public_key.

        **Validates: Requirements 8.2**
        """
        public_keys = set()

        for user_id in user_ids:
            mock_db = _make_mock_db_no_wallet()
            service = WalletService(db=mock_db)

            # Use real Keypair.random() - each call generates a unique keypair
            result = await service.create_wallet(user_id)
            public_key = result.public_key

            # Assert this public key hasn't been seen before
            assert public_key not in public_keys, (
                f"Duplicate public key {public_key} generated for user {user_id}. "
                f"All public keys must be globally unique."
            )
            public_keys.add(public_key)

        # Final check: we have as many unique keys as users
        assert len(public_keys) == len(user_ids)

    @given(user_id=uuid_strategy)
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_error_handling_is_idempotent(self, user_id: uuid.UUID):
        """Calling create_wallet after it already exists always raises
        the same WalletAlreadyExistsError with consistent properties.

        **Validates: Requirements 8.2**
        """
        mock_db = _make_mock_db_with_existing_wallet()
        service = WalletService(db=mock_db)

        # Call multiple times - should always raise the same error type
        errors = []
        for _ in range(3):
            with pytest.raises(WalletAlreadyExistsError) as exc_info:
                await service.create_wallet(user_id)
            errors.append(exc_info.value)

        # All errors should have the same status code and message
        for error in errors:
            assert error.status_code == 409
            assert "at most one wallet" in error.message

        # Error messages should be consistent across calls
        assert all(e.message == errors[0].message for e in errors)
        assert all(e.status_code == errors[0].status_code for e in errors)
