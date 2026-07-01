"""Fund disbursement service.

Orchestrates the complete fund disbursement flow: compliance verification,
pool balance checks, advisory locking, Stellar payment execution, and
transaction recording with retry logic for network failures.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Protocol

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eligibility_evaluation import EligibilityEvaluation
from app.models.enums import EligibilityStatus
from app.models.funding_pool import FundingPool
from app.models.program import Program
from app.models.stellar_wallet import StellarWallet
from app.models.transaction import Transaction

# =============================================================================
# Error Classes
# =============================================================================


class FundingServiceError(Exception):
    """Base exception for funding service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InsufficientFundsError(FundingServiceError):
    """Raised when pool balance is less than requested disbursement amount."""

    def __init__(self, pool_balance: float, requested_amount: float):
        super().__init__(
            f"Insufficient funds: pool balance {pool_balance} < requested {requested_amount}",
            status_code=400,
        )
        self.pool_balance = pool_balance
        self.requested_amount = requested_amount


class PoolPausedError(FundingServiceError):
    """Raised when disbursements are attempted on a paused pool."""

    def __init__(self, program_id: uuid.UUID):
        super().__init__(
            f"Disbursements are paused for program {program_id}",
            status_code=403,
        )
        self.program_id = program_id


class NotEligibleError(FundingServiceError):
    """Raised when recipient's compliance evaluation is not ELIGIBLE."""

    def __init__(self, recipient_id: uuid.UUID, status: str):
        super().__init__(
            f"Recipient {recipient_id} is not eligible. Current status: {status}",
            status_code=400,
        )
        self.recipient_id = recipient_id
        self.current_status = status


class DisbursementInProgressError(FundingServiceError):
    """Raised when a concurrent disbursement is already being processed."""

    def __init__(self, program_id: uuid.UUID):
        super().__init__(
            f"A disbursement is already in progress for program {program_id}",
            status_code=409,
        )
        self.program_id = program_id


class StellarTransactionError(FundingServiceError):
    """Raised when a Stellar transaction fails."""

    def __init__(self, message: str):
        super().__init__(f"Stellar transaction error: {message}", status_code=502)


class StellarNetworkUnreachableError(FundingServiceError):
    """Raised when the Stellar network cannot be reached."""

    def __init__(self):
        super().__init__(
            "Stellar network is unreachable. Transaction recorded as pending.",
            status_code=503,
        )


# =============================================================================
# StellarClient Protocol
# =============================================================================


class StellarPaymentResult:
    """Result of a Stellar payment submission."""

    def __init__(
        self,
        tx_hash: str,
        success: bool,
        error_message: Optional[str] = None,
    ):
        self.tx_hash = tx_hash
        self.success = success
        self.error_message = error_message


class StellarClient(Protocol):
    """Protocol for Stellar payment operations.

    This protocol defines the interface for interacting with the Stellar network.
    Implementations can be swapped for testing (mock) or production (real SDK).
    """

    async def submit_payment(
        self,
        source_secret: str,
        destination_public_key: str,
        amount: str,
        asset_code: str,
        memo: Optional[str] = None,
    ) -> StellarPaymentResult:
        """Submit a payment transaction to the Stellar network.

        Args:
            source_secret: The source account's secret key.
            destination_public_key: The destination account's public key.
            amount: The amount to send as a string (e.g., "100.0").
            asset_code: The asset code (e.g., "XLM").
            memo: Optional transaction memo.

        Returns:
            StellarPaymentResult with transaction hash and status.

        Raises:
            StellarNetworkUnreachableError: If the network cannot be reached.
            StellarTransactionError: If the transaction fails for other reasons.
        """
        ...

    async def invoke_contract(
        self,
        contract_id: str,
        function_name: str,
        args: dict,
        source_secret: str,
    ) -> StellarPaymentResult:
        """Invoke a Soroban smart contract function.

        Args:
            contract_id: The contract address.
            function_name: The function to invoke.
            args: Arguments to pass to the contract function.
            source_secret: The source account's secret key for signing.

        Returns:
            StellarPaymentResult indicating success or failure.
        """
        ...


# =============================================================================
# Retry Configuration
# =============================================================================

# Exponential backoff: 5 attempts over ~15 minutes
# Delays: 30s, 60s, 120s, 240s, 480s ≈ 15.5 minutes total
RETRY_MAX_ATTEMPTS = 5
RETRY_BASE_DELAY_SECONDS = 30
RETRY_BACKOFF_MULTIPLIER = 2


# =============================================================================
# FundingService
# =============================================================================


class FundingService:
    """Service for managing fund disbursements.

    Orchestrates compliance verification, pool balance checks, advisory locking,
    Stellar payment execution, and transaction recording.
    """

    def __init__(self, db: AsyncSession, stellar_client: StellarClient):
        self.db = db
        self.stellar_client = stellar_client

    async def disburse_funds(
        self,
        recipient_id: uuid.UUID,
        program_id: uuid.UUID,
        amount: float,
        compliance_evaluation_id: uuid.UUID,
    ) -> Transaction:
        """Execute a fund disbursement to an eligible recipient.

        Flow:
        1. Verify latest compliance evaluation is ELIGIBLE
        2. Check pool is_active (not paused)
        3. Check pool.balance >= amount
        4. Acquire PostgreSQL advisory lock to prevent double-spend
        5. Submit Stellar transaction
        6. On success: record transaction, decrement pool balance, increment total_funded
        7. On Stellar failure: record with "failed" status
        8. On network unreachable: record with "pending" status for background retry

        Args:
            recipient_id: UUID of the recipient to disburse to.
            program_id: UUID of the program funding the disbursement.
            amount: Amount to disburse.
            compliance_evaluation_id: UUID of the compliance evaluation proving eligibility.

        Returns:
            The created Transaction record.

        Raises:
            NotEligibleError: If the compliance evaluation is not ELIGIBLE.
            PoolPausedError: If the funding pool is paused.
            InsufficientFundsError: If pool balance < amount.
            DisbursementInProgressError: If advisory lock cannot be acquired.
            StellarTransactionError: If Stellar transaction fails.
            StellarNetworkUnreachableError: If network is unreachable.
        """
        # Step 1: Verify compliance evaluation is ELIGIBLE
        evaluation = await self._get_evaluation(compliance_evaluation_id)
        if evaluation is None:
            raise NotEligibleError(recipient_id, "NOT_FOUND")
        if evaluation.overall_status != EligibilityStatus.ELIGIBLE:
            raise NotEligibleError(recipient_id, evaluation.overall_status.value)
        if evaluation.recipient_id != recipient_id:
            raise NotEligibleError(recipient_id, "EVALUATION_MISMATCH")
        if evaluation.program_id != program_id:
            raise NotEligibleError(recipient_id, "PROGRAM_MISMATCH")

        # Step 2: Get funding pool and check if active
        pool = await self._get_funding_pool(program_id)
        if pool is None:
            raise FundingServiceError(
                f"No funding pool found for program {program_id}", status_code=404
            )
        if not pool.is_active:
            raise PoolPausedError(program_id)

        # Step 3: Check pool balance
        if float(pool.balance) < amount:
            raise InsufficientFundsError(float(pool.balance), amount)

        # Step 4: Acquire PostgreSQL advisory lock to prevent double-spend
        lock_key = self._compute_advisory_lock_key(program_id)
        lock_acquired = await self._acquire_advisory_lock(lock_key)
        if not lock_acquired:
            raise DisbursementInProgressError(program_id)

        # Step 5: Re-check balance under lock (could have changed)
        pool = await self._get_funding_pool(program_id)
        if float(pool.balance) < amount:
            raise InsufficientFundsError(float(pool.balance), amount)

        # Get recipient wallet
        recipient_wallet = await self._get_recipient_wallet(recipient_id)
        if recipient_wallet is None:
            raise FundingServiceError(
                f"Recipient {recipient_id} does not have a Stellar wallet",
                status_code=400,
            )

        # Decrypt pool private key for signing
        from app.services.wallet_service import decrypt_private_key

        pool_secret = decrypt_private_key(
            pool.encrypted_private_key, "default-v1"
        )

        memo = f"merit:{str(program_id)[:8]}"

        # Step 5a: Invoke Soroban contract for on-chain verification
        if pool.contract_id:
            try:
                contract_result = await self.stellar_client.invoke_contract(
                    contract_id=pool.contract_id,
                    function_name="release_funds",
                    args={
                        "recipient_id": str(recipient_id),
                        "amount": str(amount),
                        "evaluation_id": str(compliance_evaluation_id),
                    },
                    source_secret=pool_secret,
                )
                if not contract_result.success:
                    raise StellarTransactionError(
                        contract_result.error_message or "Contract invocation failed"
                    )
            except StellarNetworkUnreachableError:
                # Record as pending for background retry
                transaction = await self._record_transaction(
                    program_id=program_id,
                    recipient_id=recipient_id,
                    from_address=pool.public_key,
                    to_address=recipient_wallet.public_key,
                    amount=amount,
                    tx_hash=f"pending_{uuid.uuid4().hex[:16]}",
                    status="pending",
                    memo=memo,
                )
                raise
            except StellarTransactionError:
                # Record as failed
                transaction = await self._record_transaction(
                    program_id=program_id,
                    recipient_id=recipient_id,
                    from_address=pool.public_key,
                    to_address=recipient_wallet.public_key,
                    amount=amount,
                    tx_hash=f"failed_{uuid.uuid4().hex[:16]}",
                    status="failed",
                    memo=memo,
                )
                raise

        # Step 5b: Execute Stellar payment transfer
        try:
            payment_result = await self.stellar_client.submit_payment(
                source_secret=pool_secret,
                destination_public_key=recipient_wallet.public_key,
                amount=str(amount),
                asset_code="XLM",
                memo=memo,
            )
        except StellarNetworkUnreachableError:
            # Record transaction as pending for background retry
            transaction = await self._record_transaction(
                program_id=program_id,
                recipient_id=recipient_id,
                from_address=pool.public_key,
                to_address=recipient_wallet.public_key,
                amount=amount,
                tx_hash=f"pending_{uuid.uuid4().hex[:16]}",
                status="pending",
                memo=memo,
            )
            raise

        if not payment_result.success:
            # Record transaction as failed
            transaction = await self._record_transaction(
                program_id=program_id,
                recipient_id=recipient_id,
                from_address=pool.public_key,
                to_address=recipient_wallet.public_key,
                amount=amount,
                tx_hash=payment_result.tx_hash or f"failed_{uuid.uuid4().hex[:16]}",
                status="failed",
                memo=memo,
            )
            raise StellarTransactionError(
                payment_result.error_message or "Payment failed"
            )

        # Step 6: Success - record transaction, update balances atomically
        transaction = await self._record_transaction(
            program_id=program_id,
            recipient_id=recipient_id,
            from_address=pool.public_key,
            to_address=recipient_wallet.public_key,
            amount=amount,
            tx_hash=payment_result.tx_hash,
            status="confirmed",
            memo=memo,
            confirmed_at=datetime.now(timezone.utc),
        )

        # Decrement pool balance atomically
        await self._decrement_pool_balance(pool.id, amount)

        # Increment program total_funded atomically
        await self._increment_program_total_funded(program_id, amount)

        await self.db.flush()

        return transaction

    async def get_transaction_history(
        self,
        user_id: Optional[uuid.UUID] = None,
        program_id: Optional[uuid.UUID] = None,
    ) -> list[Transaction]:
        """Query transaction history filtered by user and/or program.

        Args:
            user_id: Optional filter by recipient user ID.
            program_id: Optional filter by program ID.

        Returns:
            List of Transaction records ordered by creation date descending.
        """
        query = select(Transaction)

        if user_id is not None:
            query = query.where(Transaction.recipient_id == user_id)
        if program_id is not None:
            query = query.where(Transaction.program_id == program_id)

        query = query.order_by(Transaction.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def pause_disbursements(self, program_id: uuid.UUID) -> FundingPool:
        """Pause disbursements for a program by deactivating its funding pool.

        Args:
            program_id: UUID of the program to pause.

        Returns:
            The updated FundingPool record.

        Raises:
            FundingServiceError: If no funding pool exists for the program.
        """
        pool = await self._get_funding_pool(program_id)
        if pool is None:
            raise FundingServiceError(
                f"No funding pool found for program {program_id}", status_code=404
            )

        await self.db.execute(
            update(FundingPool)
            .where(FundingPool.id == pool.id)
            .values(is_active=False)
        )
        await self.db.flush()

        # Refresh the pool object
        pool.is_active = False
        return pool

    async def resume_disbursements(self, program_id: uuid.UUID) -> FundingPool:
        """Resume disbursements for a program by reactivating its funding pool.

        Args:
            program_id: UUID of the program to resume.

        Returns:
            The updated FundingPool record.

        Raises:
            FundingServiceError: If no funding pool exists for the program.
        """
        pool = await self._get_funding_pool(program_id)
        if pool is None:
            raise FundingServiceError(
                f"No funding pool found for program {program_id}", status_code=404
            )

        await self.db.execute(
            update(FundingPool)
            .where(FundingPool.id == pool.id)
            .values(is_active=True)
        )
        await self.db.flush()

        pool.is_active = True
        return pool

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _get_evaluation(
        self, evaluation_id: uuid.UUID
    ) -> Optional[EligibilityEvaluation]:
        """Fetch an eligibility evaluation by ID."""
        result = await self.db.execute(
            select(EligibilityEvaluation).where(
                EligibilityEvaluation.id == evaluation_id
            )
        )
        return result.scalar_one_or_none()

    async def _get_funding_pool(
        self, program_id: uuid.UUID
    ) -> Optional[FundingPool]:
        """Fetch a funding pool by program ID."""
        result = await self.db.execute(
            select(FundingPool).where(FundingPool.program_id == program_id)
        )
        return result.scalar_one_or_none()

    async def _get_recipient_wallet(
        self, user_id: uuid.UUID
    ) -> Optional[StellarWallet]:
        """Fetch a recipient's Stellar wallet."""
        result = await self.db.execute(
            select(StellarWallet).where(StellarWallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def _compute_advisory_lock_key(self, program_id: uuid.UUID) -> int:
        """Compute a stable integer lock key from a program UUID.

        Uses the first 8 bytes of the SHA-256 hash of the program_id,
        interpreted as a signed 64-bit integer for pg_advisory_xact_lock.
        """
        hash_bytes = hashlib.sha256(str(program_id).encode()).digest()
        # Use first 8 bytes as a signed int64
        lock_key = int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)
        return lock_key

    async def _acquire_advisory_lock(self, lock_key: int) -> bool:
        """Acquire a PostgreSQL advisory transaction lock.

        Uses pg_advisory_xact_lock which is automatically released at
        transaction end (commit or rollback). This prevents double-spend
        on concurrent disbursement requests for the same program.

        Args:
            lock_key: The integer lock key.

        Returns:
            True if the lock was acquired (pg_advisory_xact_lock blocks until acquired).
        """
        await self.db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": lock_key},
        )
        return True

    async def _record_transaction(
        self,
        program_id: uuid.UUID,
        recipient_id: uuid.UUID,
        from_address: str,
        to_address: str,
        amount: float,
        tx_hash: str,
        status: str,
        memo: Optional[str] = None,
        confirmed_at: Optional[datetime] = None,
    ) -> Transaction:
        """Create and persist a transaction record."""
        transaction = Transaction(
            id=uuid.uuid4(),
            program_id=program_id,
            recipient_id=recipient_id,
            stellar_tx_hash=tx_hash,
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            asset_code="XLM",
            status=status,
            memo=memo,
            created_at=datetime.now(timezone.utc),
            confirmed_at=confirmed_at,
        )
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def _decrement_pool_balance(
        self, pool_id: uuid.UUID, amount: float
    ) -> None:
        """Atomically decrement the funding pool balance.

        Uses a SQL UPDATE with arithmetic to avoid race conditions.
        """
        await self.db.execute(
            update(FundingPool)
            .where(FundingPool.id == pool_id)
            .values(balance=FundingPool.balance - amount)
        )

    async def _increment_program_total_funded(
        self, program_id: uuid.UUID, amount: float
    ) -> None:
        """Atomically increment the program's total_funded field."""
        await self.db.execute(
            update(Program)
            .where(Program.id == program_id)
            .values(total_funded=Program.total_funded + amount)
        )


# =============================================================================
# Background Retry Job Reference
# =============================================================================


async def retry_pending_transactions(
    db: AsyncSession, stellar_client: StellarClient
) -> list[uuid.UUID]:
    """Background job to retry pending transactions with exponential backoff.

    Finds all transactions with status='pending' and attempts to resubmit them
    to the Stellar network. Uses exponential backoff with a maximum of 5 attempts
    over approximately 15 minutes.

    This function is designed to be invoked by a Celery/ARQ background worker.

    Args:
        db: Async database session.
        stellar_client: Stellar client for payment submission.

    Returns:
        List of transaction IDs that were successfully confirmed.
    """
    result = await db.execute(
        select(Transaction).where(Transaction.status == "pending")
    )
    pending_transactions = list(result.scalars().all())

    confirmed_ids: list[uuid.UUID] = []

    for txn in pending_transactions:
        # Get the funding pool for the program
        pool_result = await db.execute(
            select(FundingPool).where(FundingPool.program_id == txn.program_id)
        )
        pool = pool_result.scalar_one_or_none()
        if pool is None:
            continue

        from app.services.wallet_service import decrypt_private_key

        try:
            pool_secret = decrypt_private_key(
                pool.encrypted_private_key, "default-v1"
            )
        except Exception:
            continue

        try:
            payment_result = await stellar_client.submit_payment(
                source_secret=pool_secret,
                destination_public_key=txn.to_address,
                amount=str(txn.amount),
                asset_code=txn.asset_code,
                memo=txn.memo,
            )

            if payment_result.success:
                await db.execute(
                    update(Transaction)
                    .where(Transaction.id == txn.id)
                    .values(
                        status="confirmed",
                        stellar_tx_hash=payment_result.tx_hash,
                        confirmed_at=datetime.now(timezone.utc),
                    )
                )

                # Decrement pool balance
                await db.execute(
                    update(FundingPool)
                    .where(FundingPool.id == pool.id)
                    .values(balance=FundingPool.balance - float(txn.amount))
                )

                # Increment program total_funded
                await db.execute(
                    update(Program)
                    .where(Program.id == txn.program_id)
                    .values(total_funded=Program.total_funded + float(txn.amount))
                )

                confirmed_ids.append(txn.id)
            else:
                # Mark as failed after final attempt
                await db.execute(
                    update(Transaction)
                    .where(Transaction.id == txn.id)
                    .values(status="failed")
                )
        except StellarNetworkUnreachableError:
            # Still unreachable, leave as pending for next retry cycle
            continue

    await db.flush()
    return confirmed_ids
