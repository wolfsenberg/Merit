"""Recipient application API routes.

Provides endpoints for:
- POST /applications - Submit an application to a program (Recipient)
- GET /applications - List applications for the current recipient (Recipient)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.application import ApplicationResponse, CreateApplicationRequest
from app.services.application_service import ApplicationService, ApplicationServiceError

router = APIRouter()


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an application to a program",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Application rejected (not active, capacity reached, or duplicate)"},
    },
)
async def create_application(
    request: CreateApplicationRequest,
    current_user: User = Depends(require_roles(UserRole.RECIPIENT)),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Submit a new application to a funding program.

    Only recipients can submit applications. The program must be ACTIVE,
    must not have reached its max_recipients limit, and the recipient
    must not have already applied.
    """
    service = ApplicationService(db=db)
    try:
        return await service.create_application(request, current_user.id)
    except ApplicationServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "",
    response_model=list[ApplicationResponse],
    summary="List applications for the current recipient",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
    },
)
async def list_applications(
    current_user: User = Depends(require_roles(UserRole.RECIPIENT)),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationResponse]:
    """List all applications submitted by the current recipient.

    Returns applications ordered by submission date (newest first).
    """
    service = ApplicationService(db=db)
    return await service.list_applications(current_user.id)
