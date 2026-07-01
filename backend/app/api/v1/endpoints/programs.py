"""Program management API routes.

Provides endpoints for:
- POST /programs - Create a new program (Org Admin)
- GET /programs - List programs for the user's organization (Org Admin)
- GET /programs/{program_id} - Get program details (Org Admin)
- PUT /programs/{program_id} - Update program (Org Admin, DRAFT only)
- POST /programs/{program_id}/activate - Activate a DRAFT program
- POST /programs/{program_id}/pause - Pause an ACTIVE program
- POST /programs/{program_id}/resume - Resume a PAUSED program
- POST /programs/{program_id}/complete - Complete an ACTIVE program
- POST /programs/{program_id}/archive - Archive a COMPLETED program
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import ProgramStatus, UserRole
from app.models.user import User
from app.schemas.program import (
    AddRequirementRequest,
    CreateProgramRequest,
    ProgramListResponse,
    ProgramResponse,
    RequirementResponse,
    UpdateProgramRequest,
)
from app.schemas.wallet import FundingPoolCreateRequest, FundingPoolResponse
from app.services.program_service import (
    InvalidTransitionError,
    ProgramNotFoundError,
    ProgramService,
    ProgramServiceError,
)
from app.services.wallet_service import (
    FundingPoolAlreadyExistsError,
    WalletService,
    WalletServiceError,
)

router = APIRouter()


@router.post(
    "",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new program",
    responses={
        403: {"description": "Insufficient permissions"},
        422: {"description": "Validation error"},
    },
)
async def create_program(
    request: CreateProgramRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Create a new funding program in DRAFT status.

    Only Org Admins can create programs. The program is scoped to the
    admin's organization.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization",
        )

    service = ProgramService(db=db)
    try:
        return await service.create_program(request, current_user.organization_id)
    except ProgramServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "",
    response_model=ProgramListResponse,
    summary="List programs for the user's organization",
    responses={
        403: {"description": "Insufficient permissions"},
    },
)
async def list_programs(
    status_filter: Optional[ProgramStatus] = Query(None, alias="status"),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramListResponse:
    """List programs scoped to the current user's organization.

    Supports cursor-based pagination and optional status filtering.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization",
        )

    service = ProgramService(db=db)
    try:
        return await service.list_programs(
            organization_id=current_user.organization_id,
            status_filter=status_filter,
            cursor=cursor,
            limit=limit,
        )
    except ProgramServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/{program_id}",
    response_model=ProgramResponse,
    summary="Get program details",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
    },
)
async def get_program(
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Get details of a specific program.

    Org Admins can only access programs belonging to their organization.
    """
    service = ProgramService(db=db)
    try:
        program = await service.get_program(program_id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Enforce organization scoping for Org Admins
    if (
        current_user.role == UserRole.ORG_ADMIN
        and program.organization_id != current_user.organization_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: cannot access programs of another organization",
        )

    return program


@router.put(
    "/{program_id}",
    response_model=ProgramResponse,
    summary="Update a program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Program is not in DRAFT status"},
    },
)
async def update_program(
    program_id: uuid.UUID,
    request: UpdateProgramRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Update a program's fields. Only DRAFT programs can be updated."""
    service = ProgramService(db=db)

    # Check org ownership first
    try:
        program = await service.get_program(program_id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    if (
        current_user.role == UserRole.ORG_ADMIN
        and program.organization_id != current_user.organization_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: cannot access programs of another organization",
        )

    try:
        return await service.update_program(program_id, request)
    except ProgramServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{program_id}/activate",
    response_model=ProgramResponse,
    summary="Activate a DRAFT program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Invalid status transition"},
    },
)
async def activate_program(
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Activate a program that is currently in DRAFT status."""
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        return await service.activate_program(program_id)
    except (ProgramNotFoundError, InvalidTransitionError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{program_id}/pause",
    response_model=ProgramResponse,
    summary="Pause an ACTIVE program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Invalid status transition"},
    },
)
async def pause_program(
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Pause a program that is currently in ACTIVE status."""
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        return await service.pause_program(program_id)
    except (ProgramNotFoundError, InvalidTransitionError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{program_id}/resume",
    response_model=ProgramResponse,
    summary="Resume a PAUSED program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Invalid status transition"},
    },
)
async def resume_program(
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Resume a program that is currently in PAUSED status."""
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        return await service.resume_program(program_id)
    except (ProgramNotFoundError, InvalidTransitionError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{program_id}/complete",
    response_model=ProgramResponse,
    summary="Complete an ACTIVE program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Invalid status transition"},
    },
)
async def complete_program(
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Mark an ACTIVE program as COMPLETED."""
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        return await service.complete_program(program_id)
    except (ProgramNotFoundError, InvalidTransitionError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{program_id}/archive",
    response_model=ProgramResponse,
    summary="Archive a COMPLETED program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Invalid status transition"},
    },
)
async def archive_program(
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ProgramResponse:
    """Archive a program that is currently in COMPLETED status."""
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        return await service.archive_program(program_id)
    except (ProgramNotFoundError, InvalidTransitionError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{program_id}/fund",
    response_model=FundingPoolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Fund a program by creating a funding pool",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        409: {"description": "Funding pool already exists for this program"},
    },
)
async def fund_program(
    program_id: uuid.UUID,
    request: FundingPoolCreateRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> FundingPoolResponse:
    """Create a funding pool for a program on the Stellar network.

    Only Org Admins can fund programs belonging to their organization.
    Each program can have at most one funding pool.
    """
    await _check_org_ownership(program_id, current_user, db)

    wallet_service = WalletService(db=db)
    try:
        return await wallet_service.create_funding_pool(
            program_id=program_id,
            org_id=request.org_id,
            initial_amount=request.initial_amount,
        )
    except FundingPoolAlreadyExistsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except WalletServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{program_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a requirement to a program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
        422: {"description": "Validation error"},
    },
)
async def add_requirement(
    program_id: uuid.UUID,
    request: AddRequirementRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> RequirementResponse:
    """Add a requirement to a program.

    Org Admins can add requirements to programs belonging to their organization.
    Validates requirement type, condition operator, and verification frequency.
    """
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        return await service.add_requirement(program_id, request)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ProgramServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/{program_id}/requirements",
    response_model=list[RequirementResponse],
    summary="List requirements for a program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program not found"},
    },
)
async def list_requirements(
    program_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> list[RequirementResponse]:
    """List all requirements for a program.

    Org Admins can view requirements for programs belonging to their organization.
    """
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        return await service.list_requirements(program_id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/{program_id}/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a requirement from a program",
    responses={
        403: {"description": "Insufficient permissions"},
        404: {"description": "Program or requirement not found"},
    },
)
async def remove_requirement(
    program_id: uuid.UUID,
    requirement_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a requirement from a program.

    Org Admins can remove requirements from programs belonging to their organization.
    """
    await _check_org_ownership(program_id, current_user, db)
    service = ProgramService(db=db)
    try:
        await service.remove_requirement(program_id, requirement_id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ProgramServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


async def _check_org_ownership(
    program_id: uuid.UUID, current_user: User, db: AsyncSession
) -> None:
    """Verify the current user's org owns the program.

    Super Admins bypass this check.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return

    service = ProgramService(db=db)
    try:
        program = await service.get_program(program_id)
    except ProgramNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    if program.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: cannot access programs of another organization",
        )
