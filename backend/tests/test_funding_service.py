"""Unit tests for the FundingService - fund disbursement flow.

Tests cover:
- Compliance evaluation verification
- Pool balance checks
- Pool pause/resume logic
- Advisory lock acquisition
- Stellar payment submission (success, failure, unreachable)
- Transaction recording
- Atomic balance updates
- Transaction history queries
- Error classes
"""

import base64
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
sys.path.insert(0, ".")

from app.models.eligibility_evaluation import EligibilityEvaluation
from app.models.enums import EligibilityStatus
from app.models.funding_pool import FundingPool
from app.models.program import Program
from app.models.stellar_wallet import StellarWallet
from app.models.transaction import Transaction
from app.schemas.funding import (
    DisbursementRequest,
    DisbursementResponse,
    PauseDisbursementsResponse,
    TransactionHistoryItem,
)
from app.services.funding_service import (
    DisbursementInProgressError,
    FundingService,
    FundingServiceError,
    InsufficientFundsError,
    NotEligibleError,
    PoolPausedError,
    StellarNetworkUnreachableError,
    StellarPaymentResult,
    StellarTransactionError,
    retry_pending_transactions,
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
def mock_stellar_client():
    """Create a mock Stellar client."""
    client = AsyncMock()
    client.submit_payment = AsyncMock()
    client.invoke_contract = AsyncMock()
    return client


@pytest.fixture
def funding_service(mock_db, mock_stellar_client):
    """Create a FundingService instance with mocked dependencies."""
    return FundingService(db=mock_db, stellar_client=mock_stellar_client)


@pytest.fixture
def sample_ids():
    """Generate sample UUIDs for tests."""
    return {
        "recipient_id": uuid.uuid4(),
        "program_id": uuid.uuid4(),
        "evaluation_id": uuid.uuid4(),
        "pool_id": uuid.uuid4(),
        "wallet_id": uuid.uuid4(),
    }


def _make_evaluation(
    evaluation_id, recipient_id, program_id, status=EligibilityStatus.ELIGIBLE
):
    """Create a mock EligibilityEvaluation."""
    eval_mock = MagicMock(spec=EligibilityEvaluation)
    eval_mock.id = evaluation_id
    eval_mock.recipient_id = recipient_id
    eval_mock.program_id = program_id
    eval_mock.overall_status = status
    return eval_mock


def _make_pool(pool_id, program_id, balance=10000.0, is_active=True, contract_id=None):
    """Create a mock FundingPool."""
    pool = MagicMock(spec=FundingPool)
    pool.id = pool_id
    pool.program_id = program_id
    pool.balance = Decimal(str(balance))
    pool.is_active = is_active
    pool.public_key = "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGSNFHEBD9AFZQ7TM4JRS9A"
    pool.encrypted_private_key = "encrypted_data"
    pool.contract_id = contract_id
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
# Schema Validation Tests
# ============================================================


class TestFundingSchemas:
    """Tests for funding Pydantic schemas."""

    def test_disbursement_request_valid(self):
        """A valid disbursement request should pass validation."""
        req = DisbursementRequest(
            recipient_id=uuid.uuid4(),
            program_id=uuid.uuid4(),
            amount=500.0,
            compliance_evaluation_id=uuid.uuid4(),
        )
        assert req.amount == 500.0

    def test_disbursement_request_rejects_zero_amount(self):
        """Disbursement amount must be > 0."""
        with pytest.raises(Exception):
            DisbursementRequest(
                recipient_id=uuid.uuid4(),
                program_id=uuid.uuid4(),
                amount=0,
                compliance_evaluation_id=uuid.uuid4(),
            )

    def test_disbursement_request_rejects_negative_amount(self):
        """Disbursement amount must be positive."""
        with pytest.raises(Exception):
            DisbursementRequest(
                recipient_id=uuid.uuid4(),
                program_id=uuid.uuid4(),
                amount=-100.0,
                compliance_evaluation_id=uuid.uuid4(),
            )

    def test_disbursement_response_from_attributes(self):
        """DisbursementResponse should support from_attributes config."""
        resp = DisbursementResponse(
            id=uuid.uuid4(),
            program_id=uuid.uuid4(),
            recipient_id=uuid.uuid4(),
            stellar_tx_hash="abc123" * 10 + "abcd",
            from_address="G" * 56,
            to_address="G" * 56,
            amount=100.0,
            asset_code="XLM",
            status="confirmed",
            created_at=datetime.now(timezone.utc),
        )
        assert resp.status == "confirmed"

    def test_pause_disbursements_response(self):
        """PauseDisbursementsResponse schema should work."""
        resp = PauseDisbursementsResponse(
            program_id=uuid.uuid4(),
            is_active=False,
            message="Paused",
        )
        assert resp.is_active is False


# ============================================================
# Error Class Tests
# ============================================================


class TestErrorClasses:
    """Tests for funding service error classes."""

    def test_funding_service_error_base(self):
        """FundingServiceError should have message and status_code."""
        err = FundingServiceError("something went wrong", status_code=500)
        assert err.message == "something went wrong"
        assert err.status_code == 500
        assert str(err) == "something went wrong"

    def test_insufficient_funds_error(self):
        """InsufficientFundsError should report balance and requested amount."""
        err = InsufficientFundsError(pool_balance=50.0, requested_amount=100.0)
        assert err.status_code == 400
        assert err.pool_balance == 50.0
        assert err.requested_amount == 100.0
        assert "50" in err.message
        assert "100" in err.message

    def test_pool_paused_error(self):
        """PoolPausedError should report the program ID."""
        pid = uuid.uuid4()
        err = PoolPausedError(program_id=pid)
        assert err.status_code == 403
        assert str(pid) in err.message

    def test_not_eligible_error(self):
        """NotEligibleError should report recipient and status."""
        rid = uuid.uuid4()
        err = NotEligibleError(recipient_id=rid, status="ineligible")
        assert err.status_code == 400
        assert str(rid) in err.message
        assert "ineligible" in err.message

    def test_disbursement_in_progress_error(self):
        """DisbursementInProgressError should have 409 status."""
        pid = uuid.uuid4()
        err = DisbursementInProgressError(program_id=pid)
        assert err.status_code == 409

    def test_stellar_transaction_error(self):
        """StellarTransactionError should have 502 status."""
        err = StellarTransactionError("timeout")
        assert err.status_code == 502
        assert "timeout" in err.message

    def test_stellar_network_unreachable_error(self):
        """StellarNetworkUnreachableError should have 503 status."""
        err = StellarNetworkUnreachableError()
        assert err.status_code == 503


# ============================================================
# FundingService.disburse_funds Tests
# ============================================================


class TestDisburseFunds:
    """Tests for FundingService.disburse_funds."""

    @pytest.mark.asyncio
    async def test_disburse_funds_success(
        self, funding_service, mock_db, mock_stellar_client, sample_ids
    ):
        """Successful disbursement records transaction, decrements pool, increments total_funded."""
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            sample_ids["program_id"],
        )
        pool = _make_pool(sample_ids["pool_id"], sample_ids["program_id"], balance=5000.0)
        wallet = _make_wallet(sample_ids["wallet_id"], sample_ids["recipient_id"])

        # Setup mock db.execute to return appropriate results based on query
        call_count = {"value": 0}

        async def mock_execute(query, params=None):
            call_count["value"] += 1
            result = MagicMock()
            # The order of calls:
            # 1. Get evaluation
            # 2. Get funding pool (first check)
            # 3. Advisory lock
            # 4. Get funding pool (re-check under lock)
            # 5. Get recipient wallet
            # 6. Record transaction (add + flush)
            # 7. Decrement pool balance (update)
            # 8. Increment program total_funded (update)
            call_num = call_count["value"]
            if call_num == 1:
                result.scalar_one_or_none.return_value = evaluation
            elif call_num == 2:
                result.scalar_one_or_none.return_value = pool
            elif call_num == 3:
                # Advisory lock - just returns
                pass
            elif call_num == 4:
                result.scalar_one_or_none.return_value = pool
            elif call_num == 5:
                result.scalar_one_or_none.return_value = wallet
            else:
                # Updates and inserts
                pass
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        # Mock Stellar client success
        mock_stellar_client.submit_payment.return_value = StellarPaymentResult(
            tx_hash="abc123def456" * 5 + "abcd",
            success=True,
        )

        # Mock decrypt_private_key
        with patch(
            "app.services.wallet_service.decrypt_private_key",
            return_value="SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3",
        ):
            result = await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )

        # Verify transaction was recorded
        assert mock_db.add.called
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, Transaction)
        assert added_obj.status == "confirmed"
        assert added_obj.amount == 500.0

        # Verify Stellar payment was called
        mock_stellar_client.submit_payment.assert_called_once()

    @pytest.mark.asyncio
    async def test_disburse_funds_not_eligible(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise NotEligibleError if evaluation status is not ELIGIBLE."""
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            sample_ids["program_id"],
            status=EligibilityStatus.INELIGIBLE,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = evaluation
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotEligibleError) as exc_info:
            await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )
        assert "ineligible" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_disburse_funds_evaluation_not_found(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise NotEligibleError if evaluation doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotEligibleError):
            await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )

    @pytest.mark.asyncio
    async def test_disburse_funds_pool_paused(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise PoolPausedError if pool is_active is False."""
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            sample_ids["program_id"],
        )
        pool = _make_pool(
            sample_ids["pool_id"],
            sample_ids["program_id"],
            is_active=False,
        )

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

        with pytest.raises(PoolPausedError):
            await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )

    @pytest.mark.asyncio
    async def test_disburse_funds_insufficient_balance(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise InsufficientFundsError if pool balance < amount."""
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            sample_ids["program_id"],
        )
        pool = _make_pool(
            sample_ids["pool_id"],
            sample_ids["program_id"],
            balance=100.0,
        )

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

        with pytest.raises(InsufficientFundsError) as exc_info:
            await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )
        assert exc_info.value.pool_balance == 100.0
        assert exc_info.value.requested_amount == 500.0


    @pytest.mark.asyncio
    async def test_disburse_funds_stellar_failure_records_failed(
        self, funding_service, mock_db, mock_stellar_client, sample_ids
    ):
        """On Stellar payment failure, should record transaction with 'failed' status."""
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            sample_ids["program_id"],
        )
        pool = _make_pool(sample_ids["pool_id"], sample_ids["program_id"])
        wallet = _make_wallet(sample_ids["wallet_id"], sample_ids["recipient_id"])

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

        # Stellar payment fails
        mock_stellar_client.submit_payment.return_value = StellarPaymentResult(
            tx_hash="failed_hash_123456789012345678901234567890123456789012345678901234",
            success=False,
            error_message="Transaction rejected",
        )

        with patch(
            "app.services.wallet_service.decrypt_private_key",
            return_value="SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3",
        ):
            with pytest.raises(StellarTransactionError):
                await funding_service.disburse_funds(
                    recipient_id=sample_ids["recipient_id"],
                    program_id=sample_ids["program_id"],
                    amount=500.0,
                    compliance_evaluation_id=sample_ids["evaluation_id"],
                )

        # A failed transaction should have been recorded
        assert mock_db.add.called
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, Transaction)
        assert added_obj.status == "failed"

    @pytest.mark.asyncio
    async def test_disburse_funds_network_unreachable_records_pending(
        self, funding_service, mock_db, mock_stellar_client, sample_ids
    ):
        """On network unreachable, should record transaction with 'pending' status."""
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            sample_ids["program_id"],
        )
        pool = _make_pool(sample_ids["pool_id"], sample_ids["program_id"])
        wallet = _make_wallet(sample_ids["wallet_id"], sample_ids["recipient_id"])

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

        # Stellar network unreachable
        mock_stellar_client.submit_payment.side_effect = StellarNetworkUnreachableError()

        with patch(
            "app.services.wallet_service.decrypt_private_key",
            return_value="SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3",
        ):
            with pytest.raises(StellarNetworkUnreachableError):
                await funding_service.disburse_funds(
                    recipient_id=sample_ids["recipient_id"],
                    program_id=sample_ids["program_id"],
                    amount=500.0,
                    compliance_evaluation_id=sample_ids["evaluation_id"],
                )

        # A pending transaction should have been recorded
        assert mock_db.add.called
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, Transaction)
        assert added_obj.status == "pending"

    @pytest.mark.asyncio
    async def test_disburse_funds_no_wallet_raises_error(
        self, funding_service, mock_db, mock_stellar_client, sample_ids
    ):
        """Should raise FundingServiceError if recipient has no wallet."""
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            sample_ids["program_id"],
        )
        pool = _make_pool(sample_ids["pool_id"], sample_ids["program_id"])

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
                result.scalar_one_or_none.return_value = None  # No wallet
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        with pytest.raises(FundingServiceError, match="does not have a Stellar wallet"):
            await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )

    @pytest.mark.asyncio
    async def test_disburse_funds_evaluation_recipient_mismatch(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise NotEligibleError if evaluation.recipient_id != recipient_id."""
        other_recipient = uuid.uuid4()
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            other_recipient,  # Different recipient
            sample_ids["program_id"],
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = evaluation
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotEligibleError):
            await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )

    @pytest.mark.asyncio
    async def test_disburse_funds_evaluation_program_mismatch(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise NotEligibleError if evaluation.program_id != program_id."""
        other_program = uuid.uuid4()
        evaluation = _make_evaluation(
            sample_ids["evaluation_id"],
            sample_ids["recipient_id"],
            other_program,  # Different program
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = evaluation
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotEligibleError):
            await funding_service.disburse_funds(
                recipient_id=sample_ids["recipient_id"],
                program_id=sample_ids["program_id"],
                amount=500.0,
                compliance_evaluation_id=sample_ids["evaluation_id"],
            )


# ============================================================
# FundingService.get_transaction_history Tests
# ============================================================


class TestGetTransactionHistory:
    """Tests for FundingService.get_transaction_history."""

    @pytest.mark.asyncio
    async def test_get_history_by_user(self, funding_service, mock_db, sample_ids):
        """Should query transactions filtered by user_id."""
        mock_txns = [MagicMock(spec=Transaction), MagicMock(spec=Transaction)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_txns
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await funding_service.get_transaction_history(
            user_id=sample_ids["recipient_id"]
        )

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_by_program(self, funding_service, mock_db, sample_ids):
        """Should query transactions filtered by program_id."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await funding_service.get_transaction_history(
            program_id=sample_ids["program_id"]
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_history_no_filters(self, funding_service, mock_db):
        """Should return all transactions when no filters are provided."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await funding_service.get_transaction_history()

        assert result == []


# ============================================================
# FundingService.pause/resume Tests
# ============================================================


class TestPauseResumeDisbursements:
    """Tests for FundingService.pause_disbursements and resume_disbursements."""

    @pytest.mark.asyncio
    async def test_pause_disbursements_success(
        self, funding_service, mock_db, sample_ids
    ):
        """Should set pool.is_active to False."""
        pool = _make_pool(sample_ids["pool_id"], sample_ids["program_id"], is_active=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pool
        mock_db.execute.return_value = mock_result

        result = await funding_service.pause_disbursements(sample_ids["program_id"])

        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_pause_disbursements_no_pool(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise FundingServiceError if no pool exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(FundingServiceError, match="No funding pool"):
            await funding_service.pause_disbursements(sample_ids["program_id"])

    @pytest.mark.asyncio
    async def test_resume_disbursements_success(
        self, funding_service, mock_db, sample_ids
    ):
        """Should set pool.is_active to True."""
        pool = _make_pool(
            sample_ids["pool_id"], sample_ids["program_id"], is_active=False
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pool
        mock_db.execute.return_value = mock_result

        result = await funding_service.resume_disbursements(sample_ids["program_id"])

        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_resume_disbursements_no_pool(
        self, funding_service, mock_db, sample_ids
    ):
        """Should raise FundingServiceError if no pool exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(FundingServiceError, match="No funding pool"):
            await funding_service.resume_disbursements(sample_ids["program_id"])


# ============================================================
# Advisory Lock Tests
# ============================================================


class TestAdvisoryLock:
    """Tests for advisory lock computation."""

    def test_advisory_lock_key_is_deterministic(self, funding_service):
        """Same program_id should always produce the same lock key."""
        program_id = uuid.uuid4()
        key1 = funding_service._compute_advisory_lock_key(program_id)
        key2 = funding_service._compute_advisory_lock_key(program_id)
        assert key1 == key2

    def test_advisory_lock_key_different_for_different_programs(self, funding_service):
        """Different program_ids should produce different lock keys."""
        pid1 = uuid.uuid4()
        pid2 = uuid.uuid4()
        key1 = funding_service._compute_advisory_lock_key(pid1)
        key2 = funding_service._compute_advisory_lock_key(pid2)
        assert key1 != key2

    def test_advisory_lock_key_is_integer(self, funding_service):
        """Lock key should be an integer suitable for pg_advisory_xact_lock."""
        program_id = uuid.uuid4()
        key = funding_service._compute_advisory_lock_key(program_id)
        assert isinstance(key, int)


# ============================================================
# StellarPaymentResult Tests
# ============================================================


class TestStellarPaymentResult:
    """Tests for StellarPaymentResult."""

    def test_success_result(self):
        """Successful payment result has success=True."""
        result = StellarPaymentResult(tx_hash="abc123", success=True)
        assert result.tx_hash == "abc123"
        assert result.success is True
        assert result.error_message is None

    def test_failure_result(self):
        """Failed payment result has success=False and error message."""
        result = StellarPaymentResult(
            tx_hash="failed_123", success=False, error_message="Timeout"
        )
        assert result.success is False
        assert result.error_message == "Timeout"


# ============================================================
# Retry Pending Transactions Tests
# ============================================================


class TestRetryPendingTransactions:
    """Tests for retry_pending_transactions background job."""

    @pytest.mark.asyncio
    async def test_retry_confirms_pending_transaction(self):
        """Successfully retries a pending transaction and marks it as confirmed."""
        mock_db = AsyncMock()
        mock_stellar_client = AsyncMock()

        txn_id = uuid.uuid4()
        program_id = uuid.uuid4()
        pool_id = uuid.uuid4()

        # Mock pending transaction
        mock_txn = MagicMock(spec=Transaction)
        mock_txn.id = txn_id
        mock_txn.program_id = program_id
        mock_txn.to_address = "GDQP2KPQGKIHYJGXNUIYOMHARUARCA7DJT5FO2FFOOBD3XCDDB5LBER"
        mock_txn.amount = Decimal("500.0")
        mock_txn.asset_code = "XLM"
        mock_txn.memo = "merit:test1234"

        # Mock pool
        mock_pool = MagicMock(spec=FundingPool)
        mock_pool.id = pool_id
        mock_pool.encrypted_private_key = "encrypted_data"

        call_count = {"value": 0}

        async def mock_execute(query, params=None):
            call_count["value"] += 1
            result = MagicMock()
            if call_count["value"] == 1:
                # Pending transactions query
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = [mock_txn]
                result.scalars.return_value = mock_scalars
            elif call_count["value"] == 2:
                # Pool query
                result.scalar_one_or_none.return_value = mock_pool
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)
        mock_db.flush = AsyncMock()

        mock_stellar_client.submit_payment.return_value = StellarPaymentResult(
            tx_hash="confirmed_hash_abc", success=True
        )

        with patch(
            "app.services.wallet_service.decrypt_private_key",
            return_value="SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3",
        ):
            confirmed = await retry_pending_transactions(mock_db, mock_stellar_client)

        assert txn_id in confirmed

    @pytest.mark.asyncio
    async def test_retry_leaves_pending_on_network_error(self):
        """If network is still unreachable, transaction stays pending."""
        mock_db = AsyncMock()
        mock_stellar_client = AsyncMock()

        txn_id = uuid.uuid4()
        program_id = uuid.uuid4()

        mock_txn = MagicMock(spec=Transaction)
        mock_txn.id = txn_id
        mock_txn.program_id = program_id
        mock_txn.to_address = "GDEST..."
        mock_txn.amount = Decimal("100.0")
        mock_txn.asset_code = "XLM"
        mock_txn.memo = None

        mock_pool = MagicMock(spec=FundingPool)
        mock_pool.id = uuid.uuid4()
        mock_pool.encrypted_private_key = "encrypted_data"

        call_count = {"value": 0}

        async def mock_execute(query, params=None):
            call_count["value"] += 1
            result = MagicMock()
            if call_count["value"] == 1:
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = [mock_txn]
                result.scalars.return_value = mock_scalars
            elif call_count["value"] == 2:
                result.scalar_one_or_none.return_value = mock_pool
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)
        mock_db.flush = AsyncMock()

        mock_stellar_client.submit_payment.side_effect = StellarNetworkUnreachableError()

        with patch(
            "app.services.wallet_service.decrypt_private_key",
            return_value="SCZANGBA5YHTNYVVV3C7CAZMCLXPILHSE2F3RF7WRGAYRWRQDADDZNO3",
        ):
            confirmed = await retry_pending_transactions(mock_db, mock_stellar_client)

        assert confirmed == []
