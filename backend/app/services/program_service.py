"""Program service with CRUD operations, lifecycle management, and pagination."""

import uuid
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ProgramStatus
from app.models.program import Program
from app.models.program_requirement import ProgramRequirement
from app.schemas.program import (
    AddRequirementRequest,
    CreateProgramRequest,
    ProgramListResponse,
    ProgramResponse,
    RequirementResponse,
    UpdateProgramRequest,
)


class ProgramServiceError(Exception):
    """Base exception for program service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ProgramNotFoundError(ProgramServiceError):
    """Raised when a program is not found."""

    def __init__(self, program_id: uuid.UUID):
        super().__init__(f"Program {program_id} not found", status_code=404)


class InvalidTransitionError(ProgramServiceError):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, current_status: ProgramStatus, target_status: ProgramStatus):
        super().__init__(
            f"Cannot transition from {current_status.value} to {target_status.value}",
            status_code=409,
        )


# Valid status transitions: source -> set of valid targets
VALID_TRANSITIONS: dict[ProgramStatus, set[ProgramStatus]] = {
    ProgramStatus.DRAFT: {ProgramStatus.ACTIVE},
    ProgramStatus.ACTIVE: {ProgramStatus.PAUSED, ProgramStatus.COMPLETED},
    ProgramStatus.PAUSED: {ProgramStatus.ACTIVE},
    ProgramStatus.COMPLETED: {ProgramStatus.ARCHIVED},
    ProgramStatus.ARCHIVED: set(),
}


class ProgramService:
    """Service handling program lifecycle and CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_program(
        self, request: CreateProgramRequest, organization_id: uuid.UUID
    ) -> ProgramResponse:
        """Create a new program in DRAFT status.

        Args:
            request: Validated program creation data.
            organization_id: The organization this program belongs to.

        Returns:
            The created program response.
        """
        now = datetime.now(timezone.utc)
        program = Program(
            id=uuid.uuid4(),
            organization_id=organization_id,
            name=request.name,
            description=request.description,
            status=ProgramStatus.DRAFT,
            funding_amount_per_recipient=request.funding_amount_per_recipient,
            max_recipients=request.max_recipients,
            current_recipients=0,
            total_funded=0,
            start_date=request.start_date,
            end_date=request.end_date,
            created_at=now,
            updated_at=now,
        )

        self.db.add(program)
        await self.db.flush()

        return ProgramResponse.model_validate(program)

    async def get_program(self, program_id: uuid.UUID) -> ProgramResponse:
        """Get a program by ID.

        Args:
            program_id: The UUID of the program.

        Returns:
            The program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
        """
        program = await self._get_program_or_raise(program_id)
        return ProgramResponse.model_validate(program)

    async def update_program(
        self, program_id: uuid.UUID, request: UpdateProgramRequest
    ) -> ProgramResponse:
        """Update a program's fields. Only DRAFT programs can be updated.

        Args:
            program_id: The UUID of the program.
            request: The fields to update.

        Returns:
            The updated program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            ProgramServiceError: If the program is not in DRAFT status.
        """
        program = await self._get_program_or_raise(program_id)

        if program.status != ProgramStatus.DRAFT:
            raise ProgramServiceError(
                "Only programs in DRAFT status can be updated", status_code=409
            )

        update_data = request.model_dump(exclude_unset=True)

        # Validate end_date > start_date if both are being set or changed
        new_start = update_data.get("start_date", program.start_date)
        new_end = update_data.get("end_date", program.end_date)
        if new_end is not None and new_end <= new_start:
            raise ProgramServiceError("end_date must be after start_date")

        for field, value in update_data.items():
            setattr(program, field, value)

        await self.db.flush()
        return ProgramResponse.model_validate(program)

    async def activate_program(self, program_id: uuid.UUID) -> ProgramResponse:
        """Activate a DRAFT program.

        Args:
            program_id: The UUID of the program.

        Returns:
            The updated program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            InvalidTransitionError: If the program is not in DRAFT status.
        """
        return await self._transition_status(program_id, ProgramStatus.ACTIVE)

    async def pause_program(self, program_id: uuid.UUID) -> ProgramResponse:
        """Pause an ACTIVE program.

        Args:
            program_id: The UUID of the program.

        Returns:
            The updated program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            InvalidTransitionError: If the program is not in ACTIVE status.
        """
        return await self._transition_status(program_id, ProgramStatus.PAUSED)

    async def resume_program(self, program_id: uuid.UUID) -> ProgramResponse:
        """Resume a PAUSED program back to ACTIVE.

        Args:
            program_id: The UUID of the program.

        Returns:
            The updated program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            InvalidTransitionError: If the program is not in PAUSED status.
        """
        return await self._transition_status(program_id, ProgramStatus.ACTIVE)

    async def complete_program(self, program_id: uuid.UUID) -> ProgramResponse:
        """Mark an ACTIVE program as COMPLETED.

        Args:
            program_id: The UUID of the program.

        Returns:
            The updated program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            InvalidTransitionError: If the program is not in ACTIVE status.
        """
        return await self._transition_status(program_id, ProgramStatus.COMPLETED)

    async def archive_program(self, program_id: uuid.UUID) -> ProgramResponse:
        """Archive a COMPLETED program.

        Args:
            program_id: The UUID of the program.

        Returns:
            The updated program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            InvalidTransitionError: If the program is not in COMPLETED status.
        """
        return await self._transition_status(program_id, ProgramStatus.ARCHIVED)

    async def list_programs(
        self,
        organization_id: uuid.UUID,
        status_filter: Optional[ProgramStatus] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> ProgramListResponse:
        """List programs for an organization with cursor-based pagination.

        Programs are ordered by created_at descending (newest first).
        The cursor is the base64-encoded created_at timestamp of the last item.

        Args:
            organization_id: The organization to scope programs to.
            status_filter: Optional status to filter by.
            cursor: Optional pagination cursor (base64-encoded ISO timestamp).
            limit: Number of items per page (default 20, max 100).

        Returns:
            Paginated list of programs.
        """
        limit = min(limit, 100)

        conditions = [Program.organization_id == organization_id]

        if status_filter is not None:
            conditions.append(Program.status == status_filter)

        if cursor is not None:
            try:
                cursor_timestamp = datetime.fromisoformat(
                    b64decode(cursor.encode()).decode()
                )
                conditions.append(Program.created_at < cursor_timestamp)
            except (ValueError, Exception):
                raise ProgramServiceError("Invalid pagination cursor", status_code=400)

        query = (
            select(Program)
            .where(and_(*conditions))
            .order_by(Program.created_at.desc())
            .limit(limit + 1)  # Fetch one extra to determine if there's more
        )

        result = await self.db.execute(query)
        programs = list(result.scalars().all())

        has_more = len(programs) > limit
        if has_more:
            programs = programs[:limit]

        next_cursor = None
        if has_more and programs:
            last_created_at = programs[-1].created_at.isoformat()
            next_cursor = b64encode(last_created_at.encode()).decode()

        items = [ProgramResponse.model_validate(p) for p in programs]

        return ProgramListResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def add_requirement(
        self, program_id: uuid.UUID, request: AddRequirementRequest
    ) -> RequirementResponse:
        """Add a requirement to a program.

        Args:
            program_id: The UUID of the program.
            request: The requirement data to add.

        Returns:
            The created requirement response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
        """
        # Verify the program exists
        await self._get_program_or_raise(program_id)

        requirement = ProgramRequirement(
            id=uuid.uuid4(),
            program_id=program_id,
            requirement_type=request.requirement_type,
            description=request.description,
            condition_operator=request.condition_operator,
            condition_value=request.condition_value,
            is_mandatory=request.is_mandatory,
            verification_frequency=request.verification_frequency,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(requirement)
        await self.db.flush()

        return RequirementResponse.model_validate(requirement)

    async def remove_requirement(
        self, program_id: uuid.UUID, requirement_id: uuid.UUID
    ) -> None:
        """Remove a requirement from a program.

        Args:
            program_id: The UUID of the program.
            requirement_id: The UUID of the requirement to remove.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            ProgramServiceError: If the requirement is not found or doesn't belong to the program.
        """
        # Verify the program exists
        await self._get_program_or_raise(program_id)

        result = await self.db.execute(
            select(ProgramRequirement).where(
                and_(
                    ProgramRequirement.id == requirement_id,
                    ProgramRequirement.program_id == program_id,
                )
            )
        )
        requirement = result.scalar_one_or_none()

        if requirement is None:
            raise ProgramServiceError(
                f"Requirement {requirement_id} not found for program {program_id}",
                status_code=404,
            )

        await self.db.delete(requirement)
        await self.db.flush()

    async def list_requirements(
        self, program_id: uuid.UUID
    ) -> list[RequirementResponse]:
        """List all requirements for a program.

        Args:
            program_id: The UUID of the program.

        Returns:
            List of requirement responses.

        Raises:
            ProgramNotFoundError: If the program does not exist.
        """
        # Verify the program exists
        await self._get_program_or_raise(program_id)

        result = await self.db.execute(
            select(ProgramRequirement)
            .where(ProgramRequirement.program_id == program_id)
            .order_by(ProgramRequirement.created_at.asc())
        )
        requirements = list(result.scalars().all())

        return [RequirementResponse.model_validate(r) for r in requirements]

    async def _transition_status(
        self, program_id: uuid.UUID, target_status: ProgramStatus
    ) -> ProgramResponse:
        """Transition a program to the target status with guard checks.

        Args:
            program_id: The UUID of the program.
            target_status: The desired new status.

        Returns:
            The updated program response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            InvalidTransitionError: If the transition is not valid.
        """
        program = await self._get_program_or_raise(program_id)

        valid_targets = VALID_TRANSITIONS.get(program.status, set())
        if target_status not in valid_targets:
            raise InvalidTransitionError(program.status, target_status)

        program.status = target_status
        await self.db.flush()

        return ProgramResponse.model_validate(program)

    async def _get_program_or_raise(self, program_id: uuid.UUID) -> Program:
        """Fetch a program by ID or raise ProgramNotFoundError.

        Args:
            program_id: The UUID of the program.

        Returns:
            The Program model instance.

        Raises:
            ProgramNotFoundError: If the program does not exist.
        """
        result = await self.db.execute(
            select(Program).where(Program.id == program_id)
        )
        program = result.scalar_one_or_none()

        if program is None:
            raise ProgramNotFoundError(program_id)

        return program
