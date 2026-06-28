"""Compliance evaluation API routes.

Provides endpoints for:
- GET /compliance/{recipient_id}/{program_id} - Get compliance status (Org Admin)
- POST /compliance/evaluate - Trigger eligibility evaluation (Org Admin)
- POST /compliance/evaluate-batch - Trigger batch evaluation for a program (Org Admin)

Requirements: 6.1, 6.12
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_roles
from app.models.eligibility_evaluation import EligibilityEvaluation
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.compliance import (
    BatchEvaluationRequest,
    BatchEvaluationResponse,
    EligibilityEvaluationResponse,
    EvaluateEligibilityRequest,
)
from app.services.compliance_engine import EligibilityService, EligibilityServiceError

router = APIRouter()


@router.get(
    "/{recipient_id}/{program_id}",
    response_model=EligibilityEvaluationResponse,
    summary="Get compliance status for a recipient in a program",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "No evaluation found"},
    },
)
async def get_compliance_status(
    recipient_id: uuid.UUID,
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> EligibilityEvaluationResponse:
    """Get the latest compliance evaluation for a recipient in a program.

    Only Org Admins (and Super Admins) can access this endpoint.
    Returns the most recent eligibility evaluation record.
    """
    result = await db.execute(
        select(EligibilityEvaluation)
        .where(
            and_(
                EligibilityEvaluation.recipient_id == recipient_id,
                EligibilityEvaluation.program_id == program_id,
            )
        )
        .order_by(EligibilityEvaluation.evaluated_at.desc())
        .limit(1)
    )
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No compliance evaluation found for recipient {recipient_id} in program {program_id}",
        )

    return EligibilityEvaluationResponse.model_validate(evaluation)


@router.post(
    "/evaluate",
    response_model=EligibilityEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger eligibility evaluation",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        400: {"description": "Evaluation error (e.g., no requirements defined)"},
    },
)
async def trigger_evaluation(
    request: EvaluateEligibilityRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> EligibilityEvaluationResponse:
    """Trigger an eligibility evaluation for a recipient in a program.

    Evaluates all program requirements against the recipient's verified
    submissions and determines overall eligibility status.

    Only Org Admins (and Super Admins) can trigger evaluations.
    """
    service = EligibilityService(db=db)
    try:
        evaluation = await service.evaluate_eligibility(
            recipient_id=request.recipient_id,
            program_id=request.program_id,
        )
        await db.flush()
        return EligibilityEvaluationResponse.model_validate(evaluation)
    except EligibilityServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )


@router.post(
    "/evaluate-batch",
    response_model=BatchEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger batch evaluation for all recipients in a program",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        400: {"description": "Evaluation error"},
    },
)
async def trigger_batch_evaluation(
    request: BatchEvaluationRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> BatchEvaluationResponse:
    """Trigger batch eligibility evaluation for all recipients enrolled in a program.

    Evaluates every recipient with an approved or pending application for the
    specified program.

    Only Org Admins (and Super Admins) can trigger batch evaluations.
    """
    service = EligibilityService(db=db)
    try:
        evaluations = await service.evaluate_batch(program_id=request.program_id)
        await db.flush()
        results = [
            EligibilityEvaluationResponse.model_validate(e) for e in evaluations
        ]
        return BatchEvaluationResponse(
            program_id=request.program_id,
            total_evaluated=len(results),
            results=results,
            evaluated_at=datetime.utcnow(),
        )
    except EligibilityServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
