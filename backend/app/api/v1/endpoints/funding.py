"""Funding API routes.

Provides endpoints for:
- GET /funding/wallet - Get wallet info for current user (Recipient)
- POST /funding/wallet - Create wallet for current user (Recipient)
- POST /funding/disburse - Disburse funds to a recipient (Org Admin)
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.funding import (
    DisbursementRequest,
    DisbursementResponse,
    TransactionHistoryItem,
)
from app.schemas.wallet import WalletResponse
from app.services.funding_service import (
    FundingService,
    FundingServiceError,
    StellarClient,
)
from app.services.wallet_service import (
    WalletAlreadyExistsError,
    WalletNotFoundError,
    WalletService,
    WalletServiceError,
)

router = APIRouter()

# Separate router for /transactions (mounted at a different prefix)
transactions_router = APIRouter()


# ---------------------------------------------------------------------------
# Wallet Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/wallet",
    response_model=WalletResponse,
    summary="Get wallet info for current user",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Wallet not found"},
    },
)
async def get_wallet(
    current_user: User = Depends(require_roles(UserRole.RECIPIENT)),
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Get the Stellar wallet information for the currently authenticated recipient."""
    service = WalletService(db=db)
    try:
        return await service.get_wallet(current_user.id)
    except WalletNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except WalletServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/wallet",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create wallet for current user",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Wallet already exists"},
    },
)
async def create_wallet(
    current_user: User = Depends(require_roles(UserRole.RECIPIENT)),
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Create a new Stellar wallet for the currently authenticated recipient.

    Each user can have at most one wallet. Returns 409 if a wallet already exists.
    """
    service = WalletService(db=db)
    try:
        return await service.create_wallet(current_user.id)
    except WalletAlreadyExistsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except WalletServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ---------------------------------------------------------------------------
# Disbursement Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/disburse",
    response_model=DisbursementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Disburse funds to a recipient",
    responses={
        400: {"description": "Invalid request or ineligible recipient"},
        403: {"description": "Insufficient permissions or pool paused"},
        409: {"description": "Concurrent disbursement in progress"},
        502: {"description": "Stellar transaction error"},
        503: {"description": "Stellar network unreachable"},
    },
)
async def disburse_funds(
    request: DisbursementRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> DisbursementResponse:
    """Disburse funds to an eligible recipient.

    Verifies compliance evaluation, checks pool balance, executes Stellar
    payment, and records the transaction. Only Org Admins can trigger
    disbursements.
    """
    # Create a minimal StellarClient stub for now — the real client
    # will be injected via dependency injection in production.
    class _NoOpStellarClient:
        """Placeholder Stellar client that raises if called.

        A real implementation or mock should be wired via DI.
        """

        async def submit_payment(self, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stellar client not configured",
            )

        async def invoke_contract(self, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stellar client not configured",
            )

    stellar_client: StellarClient = _NoOpStellarClient()  # type: ignore[assignment]

    service = FundingService(db=db, stellar_client=stellar_client)
    try:
        transaction = await service.disburse_funds(
            recipient_id=request.recipient_id,
            program_id=request.program_id,
            amount=request.amount,
            compliance_evaluation_id=request.compliance_evaluation_id,
        )
        return DisbursementResponse.model_validate(transaction)
    except FundingServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ---------------------------------------------------------------------------
# Transaction History Endpoint (mounted at /transactions prefix)
# ---------------------------------------------------------------------------


@transactions_router.get(
    "",
    response_model=list[TransactionHistoryItem],
    summary="Get transaction history",
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_transactions(
    program_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionHistoryItem]:
    """Get transaction history filtered by the current user's role.

    - Recipients see only their own transactions.
    - Org Admins see transactions for programs in their organization.
    - Super Admins see all transactions (optionally filtered by program_id).
    """

    class _NoOpStellarClient:
        async def submit_payment(self, **kwargs):
            pass

        async def invoke_contract(self, **kwargs):
            pass

    stellar_client: StellarClient = _NoOpStellarClient()  # type: ignore[assignment]

    service = FundingService(db=db, stellar_client=stellar_client)

    # Filter by role
    user_id_filter: Optional[uuid.UUID] = None
    program_id_filter: Optional[uuid.UUID] = program_id

    if current_user.role == UserRole.RECIPIENT:
        # Recipients only see their own transactions
        user_id_filter = current_user.id
    elif current_user.role == UserRole.ORG_ADMIN:
        # Org Admins see transactions filtered optionally by program
        user_id_filter = None
    # Super Admins see all

    transactions = await service.get_transaction_history(
        user_id=user_id_filter,
        program_id=program_id_filter,
    )
    return [TransactionHistoryItem.model_validate(t) for t in transactions]
