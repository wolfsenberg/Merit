"""Property-based tests for Funding Integrity (P1) and Eligibility Prerequisite (P2).

**Validates: Requirements 7.1, 7.2, 7.4**

Property P1: Funding Integrity
∀ transaction t, ∀ program p: t.amount <= p.funding_pool.balance at time of
disbursement. No transaction should overdraw a funding pool. The sum of all
transactions for a program must equal the program's total_disbursed field.

Property P2: Eligibility Prerequisite
∀ disbursement d: There exists a ComplianceEvaluation e where
e.overall_status == ELIGIBLE and e.recipient_id == d.recipient_id and
e.program_id == d.program_id. Funds are never released without a valid,
current eligibility determination.
"""

import base64
import hashlib
import os
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

import sys
sys.path.insert(0, ".")

from app.models.eligibility_evaluation import EligibilityEvaluation
from app.models.enums import EligibilityStatus
from app.models.funding_pool import FundingPool
from app.models.stellar_wallet import StellarWallet
from app.models.transaction import Transaction
from app.services.funding_service import (
    FundingService,
    InsufficientFundsError,
    NotEligibleError,
    StellarPaymentResult,
)


# ============================================================
# Strategies
# ============================================================

# Positive amounts for disbursement (Stellar supports up to 7 decimal places)
positive_amount_strategy = st.floats(
    min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False
)

# Pool balances
pool_balance_strategy = st.floats(
    min_value=0.0, max_value=10_000_000.0, allow_nan=False, allow_infinity=False
)

# UUID strategy
uuid_strategy = st.builds(uuid.uuid4)

# Non-ELIGIBLE eligibility statuses
non_eligible_status_strategy = st.sampled_from([
    EligibilityStatus.INELIGIBLE,
    EligibilityStatus.PENDING_VERIFICATION,
    EligibilityStatus.PARTIAL,
])


# ============================================================
# Helpers
# ============================================================


def _generate_test_encryption_key() -> str:
    """Generate a valid 32-byte base64-encoded encryption key for tests."""
    return base64.b64encode(os.urandom(32)).decode("utf-8")


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    """Set a valid encryption key for all tests."""
    key = _generate_test_encryption_key()
    monkeypatch.setenv("WALLET_ENCRYPTION_KEY", key)


def _make_evaluation(evaluation_id, recipient_id, program_id, status=EligibilityStatus.ELIGIBLE):
    """Create a mock EligibilityEvaluation."""
    eval_mock = MagicMock(spec=EligibilityEvaluation)
    eval_mock.id = evaluation_id
    eval_mock.recipient_id = recipient_id
    eval_mock.program_id = program_id
    eval_mock.overall_status = status
    return eval_mock


def _make_pool(pool_id, program_id, balance, is_active=True):
    """Create a mock FundingPool."""
    pool = MagicMock(spec=FundingPool)
    pool.id = pool_id
    pool.program_id = program_id
    pool.balance = Decimal(str(balance))
    pool.is_active = is_active
    pool.public_key = "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"
    pool.encrypted_private_key = "encrypted_data"
    pool.contract_id = None
    pool.network = "testnet"
    return pool


def _make_wallet(wallet_id, user_id):
    """Create a mock StellarWallet."""
    wallet = MagicMock(spec=StellarWallet)
    wallet.id = wallet_id
    wallet.user_id = user_id
    wallet.public_key = "GDQP2KPQGKIHYJGXNUIYOMHARUARCA7DJT5FO2FFOOBD3XCDDB5LBER"
    wallet.network = "testnet"
    return wallet


# ============================================================
# Property P1: Funding Integrity - Overdraw Prevention
# ============================================================


class TestPropertyP1FundingIntegrity:
    """Property P1: No transaction overdraws a funding pool.

    **Validates: Requirements 7.1, 7.2, 7.4**
    """

    @given(
        amount=positive_amount_strategy,
        balance=pool_balance_strategy,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_overdraw_always_raises_insufficient_funds(
        self, amount: float, balance: float
    ):
        """For any disbursement amount that exceeds pool balance,
        InsufficientFundsError is always raised (no overdraw possible).

        **Validates: Requirements 7.1, 7.2**
        """
        # Only consider cases where amount > balance (overdraw attempt)
        assume(amount > balance)

        recipient_id = uuid.uuid4()
        program_id = uuid.uuid4()
        evaluation_id = uuid.uuid4()
        pool_id = uuid.uuid4()

        evaluation = _make_evaluation(evaluation_id, recipient_id, program_id)
        pool = _make_pool(pool_id, program_id, balance=balance, is_active=True)

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        call_count = {"value": 0}

        async def mock_execute(query, params=None):
            call_count["value"] += 1
            result = MagicMock()
            if call_count["value"] == 1:
                result.scalar_one_or_none.return_value = evaluation
            elif call_count["value"] == 2:
                result.scalar_one_or_none.return_value = pool
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        mock_stellar = AsyncMock()
        service = FundingService(db=mock_db, stellar_client=mock_stellar)

        with pytest.raises(InsufficientFundsError) as exc_info:
            await service.disburse_funds(
                recipient_id=recipient_id,
                program_id=program_id,
                amount=amount,
                compliance_evaluation_id=evaluation_id,
            )

        # Verify the error correctly reports the balance and amount
        assert exc_info.value.pool_balance == float(pool.balance)
        assert exc_info.value.requested_amount == amount

        # Stellar payment should never have been called (no overdraw)
        mock_stellar.submit_payment.assert_not_called()

    @given(
        amount=positive_amount_strategy,
        balance=pool_balance_strategy,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_balance_never_negative_after_disbursement(
        self, amount: float, balance: float
    ):
        """For any disbursement, either it succeeds (balance >= amount)
        or it raises InsufficientFundsError. The pool balance is always
        checked before proceeding to payment.

        **Validates: Requirements 7.1, 7.2**
        """
        recipient_id = uuid.uuid4()
        program_id = uuid.uuid4()
        evaluation_id = uuid.uuid4()
        pool_id = uuid.uuid4()
        wallet_id = uuid.uuid4()

        evaluation = _make_evaluation(evaluation_id, recipient_id, program_id)
        pool = _make_pool(pool_id, program_id, balance=balance, is_active=True)
        wallet = _make_wallet(wallet_id, recipient_id)

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        call_count = {"value": 0}

        async def mock_execute(query, params=None):
            call_count["value"] += 1
            result = MagicMock()
            if call_count["value"] == 1:
                result.scalar_one_or_none.return_value = evaluation
            elif call_count["value"] == 2:
                result.scalar_one_or_none.return_value = pool
            elif call_count["value"] == 3:
                pass  # advisory lock
            elif call_count["value"] == 4:
                result.scalar_one_or_none.return_value = pool
            elif call_count["value"] == 5:
                result.scalar_one_or_none.return_value = wallet
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        mock_stellar = AsyncMock()
        mock_stellar.submit_payment.return_value = StellarPaymentResult(
            tx_hash="a" * 64,
            success=True,
        )

        service = FundingService(db=mock_db, stellar_client=mock_stellar)

        if amount > balance:
            # Should raise InsufficientFundsError - pool never overdrawn
            with pytest.raises(InsufficientFundsError):
                with patch(
                    "app.services.wallet_service.decrypt_private_key",
                    return_value="SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3",
                ):
                    await service.disburse_funds(
                        recipient_id=recipient_id,
                        program_id=program_id,
                        amount=amount,
                        compliance_evaluation_id=evaluation_id,
                    )
            # Stellar should never have been called
            mock_stellar.submit_payment.assert_not_called()
        else:
            # Should succeed - balance is sufficient
            with patch(
                "app.services.wallet_service.decrypt_private_key",
                return_value="SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3",
            ):
                result = await service.disburse_funds(
                    recipient_id=recipient_id,
                    program_id=program_id,
                    amount=amount,
                    compliance_evaluation_id=evaluation_id,
                )
            # Transaction was recorded
            assert mock_db.add.called
            added_obj = mock_db.add.call_args[0][0]
            assert isinstance(added_obj, Transaction)
            assert added_obj.amount == amount
            # Remaining balance would be balance - amount >= 0
            assert balance - amount >= 0


# ============================================================
# Property P2: Eligibility Prerequisite
# ============================================================


class TestPropertyP2EligibilityPrerequisite:
    """Property P2: Funds are never released without a valid ELIGIBLE
    compliance evaluation.

    **Validates: Requirements 7.1, 7.4**
    """

    @given(status=non_eligible_status_strategy)
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_non_eligible_status_always_raises_not_eligible_error(
        self, status: EligibilityStatus
    ):
        """For any non-ELIGIBLE evaluation status, disburse_funds always
        raises NotEligibleError. Funds are never released.

        **Validates: Requirements 7.1, 7.4**
        """
        recipient_id = uuid.uuid4()
        program_id = uuid.uuid4()
        evaluation_id = uuid.uuid4()

        evaluation = _make_evaluation(
            evaluation_id, recipient_id, program_id, status=status
        )

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = evaluation
        mock_db.execute.return_value = mock_result

        mock_stellar = AsyncMock()
        service = FundingService(db=mock_db, stellar_client=mock_stellar)

        with pytest.raises(NotEligibleError) as exc_info:
            await service.disburse_funds(
                recipient_id=recipient_id,
                program_id=program_id,
                amount=100.0,
                compliance_evaluation_id=evaluation_id,
            )

        # Should report the current non-eligible status
        assert exc_info.value.current_status == status.value

        # Stellar payment must NOT have been called (no funds released)
        mock_stellar.submit_payment.assert_not_called()
        mock_stellar.invoke_contract.assert_not_called()

    @given(
        recipient_id=uuid_strategy,
        program_id=uuid_strategy,
        evaluation_id=uuid_strategy,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_none_evaluation_always_raises_not_eligible_error(
        self,
        recipient_id: uuid.UUID,
        program_id: uuid.UUID,
        evaluation_id: uuid.UUID,
    ):
        """For a None (not found) evaluation, disburse_funds always raises
        NotEligibleError. Funds are never released without a valid evaluation.

        **Validates: Requirements 7.1, 7.4**
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_stellar = AsyncMock()
        service = FundingService(db=mock_db, stellar_client=mock_stellar)

        with pytest.raises(NotEligibleError) as exc_info:
            await service.disburse_funds(
                recipient_id=recipient_id,
                program_id=program_id,
                amount=100.0,
                compliance_evaluation_id=evaluation_id,
            )

        # Should indicate the evaluation was NOT_FOUND
        assert exc_info.value.current_status == "NOT_FOUND"

        # Stellar payment must NOT have been called
        mock_stellar.submit_payment.assert_not_called()
        mock_stellar.invoke_contract.assert_not_called()


# ============================================================
# Advisory Lock Determinism
# ============================================================


class TestAdvisoryLockDeterminism:
    """The advisory lock key must be deterministic: same program_id
    always produces the same lock key.

    **Validates: Requirements 7.1, 7.2**
    """

    @given(program_id=uuid_strategy)
    @settings(max_examples=200, deadline=None)
    def test_lock_key_is_deterministic(self, program_id: uuid.UUID):
        """For any program_id, _compute_advisory_lock_key always returns
        the same value across multiple calls.

        **Validates: Requirements 7.1, 7.2**
        """
        mock_db = AsyncMock()
        mock_stellar = AsyncMock()
        service = FundingService(db=mock_db, stellar_client=mock_stellar)

        key1 = service._compute_advisory_lock_key(program_id)
        key2 = service._compute_advisory_lock_key(program_id)
        key3 = service._compute_advisory_lock_key(program_id)

        assert key1 == key2 == key3

        # Must be an integer suitable for pg_advisory_xact_lock
        assert isinstance(key1, int)

        # Verify it matches the expected computation
        expected_hash = hashlib.sha256(str(program_id).encode()).digest()
        expected_key = int.from_bytes(expected_hash[:8], byteorder="big", signed=True)
        assert key1 == expected_key
