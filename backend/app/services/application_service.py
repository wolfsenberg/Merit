"""Application service handling recipient applications to funding programs."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.enums import ApplicationStatus, ProgramStatus
from app.models.program import Program
from app.schemas.application import ApplicationResponse, CreateApplicationRequest


class ApplicationServiceError(Exception):
    """Base exception for application service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ProgramNotActiveError(ApplicationServiceError):
    """Raised when trying to apply to a non-ACTIVE program."""

    def __init__(self, program_id: uuid.UUID, current_status: ProgramStatus):
        super().__init__(
            f"Program {program_id} is not accepting applications (status: {current_status.value})",
            status_code=409,
        )


class ProgramCapacityReachedError(ApplicationServiceError):
    """Raised when a program has reached its max_recipients limit."""

    def __init__(self, program_id: uuid.UUID):
        super().__init__(
            f"Program {program_id} has reached its maximum recipient capacity",
            status_code=409,
        )


class DuplicateApplicationError(ApplicationServiceError):
    """Raised when a recipient tries to apply to the same program twice."""

    def __init__(self, program_id: uuid.UUID):
        super().__init__(
            f"You have already applied to program {program_id}",
            status_code=409,
        )


class ProgramNotFoundError(ApplicationServiceError):
    """Raised when the specified program does not exist."""

    def __init__(self, program_id: uuid.UUID):
        super().__init__(
            f"Program {program_id} not found",
            status_code=404,
        )


class ApplicationService:
    """Service handling recipient application operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_application(
        self, request: CreateApplicationRequest, recipient_id: uuid.UUID
    ) -> ApplicationResponse:
        """Create a new application for a recipient to a program.

        Business rules:
        - Only ACTIVE programs accept applications
        - Program must not have reached max_recipients
        - Recipient cannot apply to the same program twice

        Args:
            request: Validated application creation data.
            recipient_id: The UUID of the applying recipient.

        Returns:
            The created application response.

        Raises:
            ProgramNotFoundError: If the program does not exist.
            ProgramNotActiveError: If the program is not in ACTIVE status.
            ProgramCapacityReachedError: If the program is at capacity.
            DuplicateApplicationError: If the recipient already applied.
        """
        # Fetch the program
        program = await self._get_program_or_raise(request.program_id)

        # Check program is ACTIVE
        if program.status != ProgramStatus.ACTIVE:
            raise ProgramNotActiveError(program.id, program.status)

        # Check capacity
        if program.current_recipients >= program.max_recipients:
            raise ProgramCapacityReachedError(program.id)

        # Check for duplicate application
        existing = await self._get_existing_application(recipient_id, request.program_id)
        if existing is not None:
            raise DuplicateApplicationError(request.program_id)

        # Create the application
        now = datetime.now(timezone.utc)
        application = Application(
            id=uuid.uuid4(),
            recipient_id=recipient_id,
            program_id=request.program_id,
            status=ApplicationStatus.PENDING,
            submitted_at=now,
        )

        self.db.add(application)
        await self.db.flush()

        return ApplicationResponse.model_validate(application)

    async def list_applications(
        self, recipient_id: uuid.UUID
    ) -> list[ApplicationResponse]:
        """List all applications for a specific recipient.

        Args:
            recipient_id: The UUID of the recipient.

        Returns:
            List of application responses ordered by submission date (newest first).
        """
        result = await self.db.execute(
            select(Application)
            .where(Application.recipient_id == recipient_id)
            .order_by(Application.submitted_at.desc())
        )
        applications = list(result.scalars().all())
        return [ApplicationResponse.model_validate(a) for a in applications]

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

    async def _get_existing_application(
        self, recipient_id: uuid.UUID, program_id: uuid.UUID
    ) -> Application | None:
        """Check if a recipient already has an application for a program.

        Args:
            recipient_id: The UUID of the recipient.
            program_id: The UUID of the program.

        Returns:
            The existing Application or None.
        """
        result = await self.db.execute(
            select(Application).where(
                and_(
                    Application.recipient_id == recipient_id,
                    Application.program_id == program_id,
                )
            )
        )
        return result.scalar_one_or_none()
