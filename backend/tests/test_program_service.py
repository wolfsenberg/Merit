"""Unit tests for program service - CRUD operations and lifecycle management."""

import uuid
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
sys.path.insert(0, ".")

from app.models.enums import ProgramStatus
from app.models.program import Program
from app.schemas.program import (
    CreateProgramRequest,
    ProgramListResponse,
    ProgramResponse,
    UpdateProgramRequest,
)
from app.services.program_service import (
    InvalidTransitionError,
    ProgramNotFoundError,
    ProgramService,
    ProgramServiceError,
    VALID_TRANSITIONS,
)


# ============================================================
# Schema Validation Tests
# ============================================================


class TestCreateProgramSchema:
    """Tests for CreateProgramRequest Pydantic validation."""

    def test_valid_creation_request(self):
        """A valid request should pass validation."""
        request = CreateProgramRequest(
            name="Test Program",
            description="A test funding program",
            funding_amount_per_recipient=1000.0,
            max_recipients=50,
            start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )
        assert request.name == "Test Program"
        assert request.funding_amount_per_recipient == 1000.0

    def test_funding_amount_must_be_positive(self):
        """funding_amount_per_recipient <= 0 should be rejected."""
        with pytest.raises(Exception):
            CreateProgramRequest(
                name="Test",
                description="Test",
                funding_amount_per_recipient=0,
                max_recipients=10,
                start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )

    def test_funding_amount_negative_rejected(self):
        """Negative funding amount should be rejected."""
        with pytest.raises(Exception):
            CreateProgramRequest(
                name="Test",
                description="Test",
                funding_amount_per_recipient=-100.0,
                max_recipients=10,
                start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )

    def test_max_recipients_must_be_at_least_one(self):
        """max_recipients < 1 should be rejected."""
        with pytest.raises(Exception):
            CreateProgramRequest(
                name="Test",
                description="Test",
                funding_amount_per_recipient=1000.0,
                max_recipients=0,
                start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )

    def test_end_date_must_be_after_start_date(self):
        """end_date <= start_date should be rejected."""
        with pytest.raises(Exception):
            CreateProgramRequest(
                name="Test",
                description="Test",
                funding_amount_per_recipient=1000.0,
                max_recipients=10,
                start_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
                end_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )

    def test_end_date_equal_to_start_date_rejected(self):
        """end_date == start_date should be rejected."""
        same_date = datetime(2025, 6, 1, tzinfo=timezone.utc)
        with pytest.raises(Exception):
            CreateProgramRequest(
                name="Test",
                description="Test",
                funding_amount_per_recipient=1000.0,
                max_recipients=10,
                start_date=same_date,
                end_date=same_date,
            )

    def test_end_date_optional(self):
        """end_date is optional and can be None."""
        request = CreateProgramRequest(
            name="Test",
            description="Test",
            funding_amount_per_recipient=1000.0,
            max_recipients=10,
            start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        assert request.end_date is None


# ============================================================
# Status Lifecycle Transition Map Tests
# ============================================================


class TestStatusTransitionMap:
    """Tests for the VALID_TRANSITIONS map correctness."""

    def test_draft_can_only_go_to_active(self):
        """DRAFT programs can only transition to ACTIVE."""
        assert VALID_TRANSITIONS[ProgramStatus.DRAFT] == {ProgramStatus.ACTIVE}

    def test_active_can_go_to_paused_or_completed(self):
        """ACTIVE programs can transition to PAUSED or COMPLETED."""
        assert VALID_TRANSITIONS[ProgramStatus.ACTIVE] == {
            ProgramStatus.PAUSED,
            ProgramStatus.COMPLETED,
        }

    def test_paused_can_go_back_to_active(self):
        """PAUSED programs can only transition back to ACTIVE."""
        assert VALID_TRANSITIONS[ProgramStatus.PAUSED] == {ProgramStatus.ACTIVE}

    def test_completed_can_only_go_to_archived(self):
        """COMPLETED programs can only transition to ARCHIVED."""
        assert VALID_TRANSITIONS[ProgramStatus.COMPLETED] == {ProgramStatus.ARCHIVED}

    def test_archived_has_no_transitions(self):
        """ARCHIVED programs cannot transition to any state."""
        assert VALID_TRANSITIONS[ProgramStatus.ARCHIVED] == set()


# ============================================================
# Program Service Tests (using mock DB)
# ============================================================


def _make_program(
    status: ProgramStatus = ProgramStatus.DRAFT,
    org_id: uuid.UUID = None,
    created_at: datetime = None,
) -> Program:
    """Helper to create a Program model for testing."""
    program = Program()
    program.id = uuid.uuid4()
    program.organization_id = org_id or uuid.uuid4()
    program.name = "Test Program"
    program.description = "Test Description"
    program.status = status
    program.funding_amount_per_recipient = 1000.0
    program.max_recipients = 50
    program.current_recipients = 0
    program.total_funded = 0
    program.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    program.end_date = datetime(2025, 12, 31, tzinfo=timezone.utc)
    program.created_at = created_at or datetime.now(timezone.utc)
    program.updated_at = datetime.now(timezone.utc)
    return program


def _mock_db_with_program(program: Program):
    """Create a mock async session that returns the given program."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = program
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


class TestProgramServiceCreate:
    """Tests for ProgramService.create_program."""

    @pytest.mark.asyncio
    async def test_create_program_in_draft_status(self):
        """A created program should always start in DRAFT status."""
        db = AsyncMock()
        db.flush = AsyncMock()
        db.add = MagicMock()

        service = ProgramService(db=db)
        request = CreateProgramRequest(
            name="New Program",
            description="Description",
            funding_amount_per_recipient=500.0,
            max_recipients=100,
            start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )

        result = await service.create_program(request, uuid.uuid4())

        assert result.status == ProgramStatus.DRAFT
        assert result.name == "New Program"
        assert result.current_recipients == 0
        assert result.total_funded == 0
        db.add.assert_called_once()
        db.flush.assert_awaited_once()


class TestProgramServiceTransitions:
    """Tests for program status transition methods."""

    @pytest.mark.asyncio
    async def test_activate_draft_program(self):
        """Activating a DRAFT program should succeed."""
        program = _make_program(ProgramStatus.DRAFT)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        result = await service.activate_program(program.id)
        assert result.status == ProgramStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activate_non_draft_raises_error(self):
        """Activating a non-DRAFT program should raise InvalidTransitionError."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        with pytest.raises(InvalidTransitionError):
            await service.activate_program(program.id)

    @pytest.mark.asyncio
    async def test_pause_active_program(self):
        """Pausing an ACTIVE program should succeed."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        result = await service.pause_program(program.id)
        assert result.status == ProgramStatus.PAUSED

    @pytest.mark.asyncio
    async def test_pause_non_active_raises_error(self):
        """Pausing a non-ACTIVE program should raise InvalidTransitionError."""
        program = _make_program(ProgramStatus.DRAFT)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        with pytest.raises(InvalidTransitionError):
            await service.pause_program(program.id)

    @pytest.mark.asyncio
    async def test_resume_paused_program(self):
        """Resuming a PAUSED program should transition back to ACTIVE."""
        program = _make_program(ProgramStatus.PAUSED)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        result = await service.resume_program(program.id)
        assert result.status == ProgramStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_resume_non_paused_raises_error(self):
        """Resuming a non-PAUSED program should raise InvalidTransitionError."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        with pytest.raises(InvalidTransitionError):
            await service.resume_program(program.id)

    @pytest.mark.asyncio
    async def test_complete_active_program(self):
        """Completing an ACTIVE program should succeed."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        result = await service.complete_program(program.id)
        assert result.status == ProgramStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_archive_completed_program(self):
        """Archiving a COMPLETED program should succeed."""
        program = _make_program(ProgramStatus.COMPLETED)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        result = await service.archive_program(program.id)
        assert result.status == ProgramStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_archive_non_completed_raises_error(self):
        """Archiving a non-COMPLETED program should raise InvalidTransitionError."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        with pytest.raises(InvalidTransitionError):
            await service.archive_program(program.id)


class TestProgramServiceGet:
    """Tests for ProgramService.get_program."""

    @pytest.mark.asyncio
    async def test_get_existing_program(self):
        """Getting an existing program should return its details."""
        program = _make_program()
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        result = await service.get_program(program.id)
        assert result.id == program.id
        assert result.name == program.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_program_raises_error(self):
        """Getting a nonexistent program should raise ProgramNotFoundError."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        service = ProgramService(db=db)

        with pytest.raises(ProgramNotFoundError):
            await service.get_program(uuid.uuid4())


class TestProgramServiceUpdate:
    """Tests for ProgramService.update_program."""

    @pytest.mark.asyncio
    async def test_update_draft_program(self):
        """Updating a DRAFT program should succeed."""
        program = _make_program(ProgramStatus.DRAFT)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        request = UpdateProgramRequest(name="Updated Name")
        result = await service.update_program(program.id, request)
        assert result.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_non_draft_raises_error(self):
        """Updating a non-DRAFT program should raise ProgramServiceError."""
        program = _make_program(ProgramStatus.ACTIVE)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        request = UpdateProgramRequest(name="Updated Name")
        with pytest.raises(ProgramServiceError) as exc_info:
            await service.update_program(program.id, request)
        assert "DRAFT" in exc_info.value.message


class TestProgramServiceList:
    """Tests for ProgramService.list_programs with cursor-based pagination."""

    @pytest.mark.asyncio
    async def test_list_returns_programs(self):
        """Listing programs should return items from the database."""
        org_id = uuid.uuid4()
        programs = [_make_program(org_id=org_id) for _ in range(3)]

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = programs
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        service = ProgramService(db=db)
        result = await service.list_programs(organization_id=org_id)

        assert len(result.items) == 3
        assert result.has_more is False
        assert result.next_cursor is None

    @pytest.mark.asyncio
    async def test_list_with_pagination(self):
        """When there are more items than limit, has_more should be True."""
        org_id = uuid.uuid4()
        # Return limit+1 programs to trigger has_more
        programs = [_make_program(org_id=org_id) for _ in range(3)]

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = programs
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)

        service = ProgramService(db=db)
        result = await service.list_programs(organization_id=org_id, limit=2)

        assert len(result.items) == 2
        assert result.has_more is True
        assert result.next_cursor is not None

    @pytest.mark.asyncio
    async def test_list_with_invalid_cursor(self):
        """An invalid cursor should raise ProgramServiceError."""
        db = AsyncMock()
        service = ProgramService(db=db)

        with pytest.raises(ProgramServiceError) as exc_info:
            await service.list_programs(
                organization_id=uuid.uuid4(), cursor="not-valid-base64!@#$"
            )
        assert "cursor" in exc_info.value.message.lower()
