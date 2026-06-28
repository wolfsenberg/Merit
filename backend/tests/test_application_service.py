"""Unit tests for application service - recipient application flow."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

import sys
sys.path.insert(0, ".")

from app.models.application import Application
from app.models.enums import ApplicationStatus, ProgramStatus
from app.models.program import Program
from app.schemas.application import ApplicationResponse, CreateApplicationRequest
from app.services.application_service import (
    ApplicationService,
    ApplicationServiceError,
    DuplicateApplicationError,
    ProgramCapacityReachedError,
    ProgramNotActiveError,
    ProgramNotFoundError,
)


# ============================================================
# Helpers
# ============================================================


def _make_program(
    status: ProgramStatus = ProgramStatus.ACTIVE,
    max_recipients: int = 50,
    current_recipients: int = 0,
) -> Program:
    """Create a Program model instance for testing."""
    program = Program()
    program.id = uuid.uuid4()
    program.organization_id = uuid.uuid4()
    program.name = "Test Program"
    program.description = "A test funding program"
    program.status = status
    program.funding_amount_per_recipient = 1000.0
    program.max_recipients = max_recipients
    program.current_recipients = current_recipients
    program.total_funded = 0
    program.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    program.end_date = datetime(2025, 12, 31, tzinfo=timezone.utc)
    program.created_at = datetime.now(timezone.utc)
    program.updated_at = datetime.now(timezone.utc)
    return program


def _mock_db_program_found(program: Program, existing_application=None):
    """Create a mock DB that returns the program on first execute, application on second."""
    db = AsyncMock()

    # Track call count to return different results
    call_count = {"value": 0}

    async def mock_execute(query):
        call_count["value"] += 1
        mock_result = MagicMock()
        if call_count["value"] == 1:
            # First call: fetch program
            mock_result.scalar_one_or_none.return_value = program
        else:
            # Second call: check existing application
            mock_result.scalar_one_or_none.return_value = existing_application
        return mock_result

    db.execute = mock_execute
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


def _mock_db_program_not_found():
    """Create a mock DB that returns None for program lookup."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


def _mock_db_for_list(applications: list[Application]):
    """Create a mock DB that returns a list of applications."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = applications
    mock_result.scalars.return_value = mock_scalars
    db.execute = AsyncMock(return_value=mock_result)
    return db


# ============================================================
# Schema Validation Tests
# ============================================================


class TestCreateApplicationSchema:
    """Tests for CreateApplicationRequest Pydantic validation."""

    def test_valid_request(self):
        """A valid request with a program_id should pass validation."""
        program_id = uuid.uuid4()
        request = CreateApplicationRequest(program_id=program_id)
        assert request.program_id == program_id

    def test_invalid_program_id_rejected(self):
        """An invalid UUID string should be rejected."""
        with pytest.raises(Exception):
            CreateApplicationRequest(program_id="not-a-uuid")


# ============================================================
# ApplicationService.create_application Tests
# ============================================================


class TestApplicationServiceCreate:
    """Tests for ApplicationService.create_application."""

    @pytest.mark.asyncio
    async def test_successful_application_to_active_program(self):
        """A recipient can successfully apply to an ACTIVE program."""
        program = _make_program(ProgramStatus.ACTIVE, max_recipients=50, current_recipients=0)
        db = _mock_db_program_found(program, existing_application=None)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)
        recipient_id = uuid.uuid4()

        result = await service.create_application(request, recipient_id)

        assert result.recipient_id == recipient_id
        assert result.program_id == program.id
        assert result.status == ApplicationStatus.PENDING
        assert result.submitted_at is not None
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_application_rejected_for_non_active_program_draft(self):
        """Applying to a DRAFT program should raise ProgramNotActiveError."""
        program = _make_program(ProgramStatus.DRAFT)
        db = _mock_db_program_found(program)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        with pytest.raises(ProgramNotActiveError) as exc_info:
            await service.create_application(request, uuid.uuid4())
        assert "not accepting applications" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_application_rejected_for_non_active_program_paused(self):
        """Applying to a PAUSED program should raise ProgramNotActiveError."""
        program = _make_program(ProgramStatus.PAUSED)
        db = _mock_db_program_found(program)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        with pytest.raises(ProgramNotActiveError):
            await service.create_application(request, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_application_rejected_for_non_active_program_completed(self):
        """Applying to a COMPLETED program should raise ProgramNotActiveError."""
        program = _make_program(ProgramStatus.COMPLETED)
        db = _mock_db_program_found(program)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        with pytest.raises(ProgramNotActiveError):
            await service.create_application(request, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_application_rejected_for_non_active_program_archived(self):
        """Applying to an ARCHIVED program should raise ProgramNotActiveError."""
        program = _make_program(ProgramStatus.ARCHIVED)
        db = _mock_db_program_found(program)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        with pytest.raises(ProgramNotActiveError):
            await service.create_application(request, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_application_rejected_when_capacity_reached(self):
        """Applying when current_recipients >= max_recipients should raise ProgramCapacityReachedError."""
        program = _make_program(ProgramStatus.ACTIVE, max_recipients=10, current_recipients=10)
        db = _mock_db_program_found(program)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        with pytest.raises(ProgramCapacityReachedError) as exc_info:
            await service.create_application(request, uuid.uuid4())
        assert "maximum recipient capacity" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_application_rejected_when_over_capacity(self):
        """Applying when current_recipients > max_recipients should also be rejected."""
        program = _make_program(ProgramStatus.ACTIVE, max_recipients=5, current_recipients=7)
        db = _mock_db_program_found(program)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        with pytest.raises(ProgramCapacityReachedError):
            await service.create_application(request, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_duplicate_application_rejected(self):
        """A recipient cannot apply to the same program twice."""
        program = _make_program(ProgramStatus.ACTIVE)
        existing_app = Application()
        existing_app.id = uuid.uuid4()
        existing_app.recipient_id = uuid.uuid4()
        existing_app.program_id = program.id
        existing_app.status = ApplicationStatus.PENDING
        existing_app.submitted_at = datetime.now(timezone.utc)

        db = _mock_db_program_found(program, existing_application=existing_app)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        with pytest.raises(DuplicateApplicationError) as exc_info:
            await service.create_application(request, existing_app.recipient_id)
        assert "already applied" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_application_to_nonexistent_program_raises_not_found(self):
        """Applying to a program that doesn't exist should raise ProgramNotFoundError."""
        db = _mock_db_program_not_found()

        service = ApplicationService(db=db)
        fake_program_id = uuid.uuid4()
        request = CreateApplicationRequest(program_id=fake_program_id)

        with pytest.raises(ProgramNotFoundError) as exc_info:
            await service.create_application(request, uuid.uuid4())
        assert "not found" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_application_records_timestamp(self):
        """The submitted_at timestamp should be set to the current time."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_program_found(program, existing_application=None)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        before = datetime.now(timezone.utc)
        result = await service.create_application(request, uuid.uuid4())
        after = datetime.now(timezone.utc)

        assert before <= result.submitted_at <= after

    @pytest.mark.asyncio
    async def test_application_initial_status_is_pending(self):
        """A new application should always have PENDING status."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_program_found(program, existing_application=None)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        result = await service.create_application(request, uuid.uuid4())
        assert result.status == ApplicationStatus.PENDING

    @pytest.mark.asyncio
    async def test_application_at_boundary_capacity(self):
        """Applying when current_recipients is exactly max_recipients - 1 should succeed."""
        program = _make_program(ProgramStatus.ACTIVE, max_recipients=10, current_recipients=9)
        db = _mock_db_program_found(program, existing_application=None)

        service = ApplicationService(db=db)
        request = CreateApplicationRequest(program_id=program.id)

        result = await service.create_application(request, uuid.uuid4())
        assert result.status == ApplicationStatus.PENDING


# ============================================================
# ApplicationService.list_applications Tests
# ============================================================


class TestApplicationServiceList:
    """Tests for ApplicationService.list_applications."""

    @pytest.mark.asyncio
    async def test_list_returns_recipient_applications(self):
        """Listing should return all applications for the given recipient."""
        recipient_id = uuid.uuid4()
        apps = []
        for _ in range(3):
            app = Application()
            app.id = uuid.uuid4()
            app.recipient_id = recipient_id
            app.program_id = uuid.uuid4()
            app.status = ApplicationStatus.PENDING
            app.submitted_at = datetime.now(timezone.utc)
            app.reviewed_at = None
            app.reviewed_by = None
            apps.append(app)

        db = _mock_db_for_list(apps)
        service = ApplicationService(db=db)

        result = await service.list_applications(recipient_id)
        assert len(result) == 3
        for app_response in result:
            assert app_response.recipient_id == recipient_id

    @pytest.mark.asyncio
    async def test_list_returns_empty_for_no_applications(self):
        """Listing should return an empty list when the recipient has no applications."""
        db = _mock_db_for_list([])
        service = ApplicationService(db=db)

        result = await service.list_applications(uuid.uuid4())
        assert result == []


# ============================================================
# Error class tests
# ============================================================


class TestApplicationServiceErrors:
    """Tests for error class properties."""

    def test_program_not_active_error_status_code(self):
        """ProgramNotActiveError should have status 409."""
        err = ProgramNotActiveError(uuid.uuid4(), ProgramStatus.DRAFT)
        assert err.status_code == 409

    def test_program_capacity_reached_error_status_code(self):
        """ProgramCapacityReachedError should have status 409."""
        err = ProgramCapacityReachedError(uuid.uuid4())
        assert err.status_code == 409

    def test_duplicate_application_error_status_code(self):
        """DuplicateApplicationError should have status 409."""
        err = DuplicateApplicationError(uuid.uuid4())
        assert err.status_code == 409

    def test_program_not_found_error_status_code(self):
        """ProgramNotFoundError should have status 404."""
        err = ProgramNotFoundError(uuid.uuid4())
        assert err.status_code == 404
