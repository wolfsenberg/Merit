"""Unit tests for requirement management - add, remove, and list requirements."""

import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, ".")

from app.models.enums import ProgramStatus, RequirementType
from app.models.program import Program
from app.models.program_requirement import ProgramRequirement
from app.schemas.program import (
    VALID_CONDITION_OPERATORS,
    VALID_VERIFICATION_FREQUENCIES,
    AddRequirementRequest,
    RequirementResponse,
)
from app.services.program_service import (
    ProgramNotFoundError,
    ProgramService,
    ProgramServiceError,
)

# ============================================================
# Schema Validation Tests
# ============================================================


class TestAddRequirementSchema:
    """Tests for AddRequirementRequest Pydantic validation."""

    def test_valid_requirement_request(self):
        """A valid requirement request should pass validation."""
        request = AddRequirementRequest(
            requirement_type=RequirementType.ACADEMIC_GWA,
            description="GWA must be at most 2.0",
            condition_operator="lte",
            condition_value="2.0",
            is_mandatory=True,
            verification_frequency="per_semester",
        )
        assert request.requirement_type == RequirementType.ACADEMIC_GWA
        assert request.condition_operator == "lte"
        assert request.is_mandatory is True

    def test_all_requirement_types_accepted(self):
        """All RequirementType enum values should be accepted."""
        for req_type in RequirementType:
            request = AddRequirementRequest(
                requirement_type=req_type,
                description="Test requirement",
                condition_operator="eq",
                condition_value="test",
                is_mandatory=True,
                verification_frequency="once",
            )
            assert request.requirement_type == req_type

    def test_all_valid_condition_operators_accepted(self):
        """All valid condition operators should be accepted."""
        for operator in VALID_CONDITION_OPERATORS:
            request = AddRequirementRequest(
                requirement_type=RequirementType.CUSTOM,
                description="Test",
                condition_operator=operator,
                condition_value="test",
                is_mandatory=True,
                verification_frequency="once",
            )
            assert request.condition_operator == operator

    def test_invalid_condition_operator_rejected(self):
        """Invalid condition operators should be rejected."""
        with pytest.raises(Exception) as exc_info:
            AddRequirementRequest(
                requirement_type=RequirementType.ACADEMIC_GWA,
                description="Test",
                condition_operator="invalid_op",
                condition_value="2.0",
                is_mandatory=True,
                verification_frequency="once",
            )
        assert "condition_operator" in str(exc_info.value).lower()

    def test_all_valid_verification_frequencies_accepted(self):
        """All valid verification frequencies should be accepted."""
        for freq in VALID_VERIFICATION_FREQUENCIES:
            request = AddRequirementRequest(
                requirement_type=RequirementType.CUSTOM,
                description="Test",
                condition_operator="eq",
                condition_value="test",
                is_mandatory=True,
                verification_frequency=freq,
            )
            assert request.verification_frequency == freq

    def test_invalid_verification_frequency_rejected(self):
        """Invalid verification frequencies should be rejected."""
        with pytest.raises(Exception) as exc_info:
            AddRequirementRequest(
                requirement_type=RequirementType.ACADEMIC_GWA,
                description="Test",
                condition_operator="lte",
                condition_value="2.0",
                is_mandatory=True,
                verification_frequency="daily",
            )
        assert "verification_frequency" in str(exc_info.value).lower()

    def test_empty_description_rejected(self):
        """Empty description should be rejected."""
        with pytest.raises(Exception):
            AddRequirementRequest(
                requirement_type=RequirementType.ACADEMIC_GWA,
                description="",
                condition_operator="lte",
                condition_value="2.0",
                is_mandatory=True,
                verification_frequency="once",
            )

    def test_is_mandatory_defaults_to_true(self):
        """is_mandatory should default to True when not specified."""
        request = AddRequirementRequest(
            requirement_type=RequirementType.ATTENDANCE,
            description="Attendance requirement",
            condition_operator="gte",
            condition_value="80",
            verification_frequency="monthly",
        )
        assert request.is_mandatory is True

    def test_is_mandatory_can_be_false(self):
        """is_mandatory can be explicitly set to False."""
        request = AddRequirementRequest(
            requirement_type=RequirementType.ATTENDANCE,
            description="Optional attendance",
            condition_operator="gte",
            condition_value="80",
            is_mandatory=False,
            verification_frequency="monthly",
        )
        assert request.is_mandatory is False


# ============================================================
# Service Tests
# ============================================================


def _make_program(
    status: ProgramStatus = ProgramStatus.DRAFT,
    org_id: uuid.UUID = None,
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
    program.created_at = datetime.now(timezone.utc)
    program.updated_at = datetime.now(timezone.utc)
    return program


def _make_requirement(
    program_id: uuid.UUID,
    requirement_type: RequirementType = RequirementType.ACADEMIC_GWA,
) -> ProgramRequirement:
    """Helper to create a ProgramRequirement model for testing."""
    req = ProgramRequirement()
    req.id = uuid.uuid4()
    req.program_id = program_id
    req.requirement_type = requirement_type
    req.description = "Test requirement"
    req.condition_operator = "lte"
    req.condition_value = "2.0"
    req.is_mandatory = True
    req.verification_frequency = "per_semester"
    req.created_at = datetime.now(timezone.utc)
    return req


def _mock_db_with_program(program: Program):
    """Create a mock async session that returns the given program."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = program
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


class TestProgramServiceAddRequirement:
    """Tests for ProgramService.add_requirement."""

    @pytest.mark.asyncio
    async def test_add_requirement_to_existing_program(self):
        """Adding a requirement to an existing program should succeed."""
        program = _make_program()
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        request = AddRequirementRequest(
            requirement_type=RequirementType.ACADEMIC_GWA,
            description="GWA must be at most 2.0",
            condition_operator="lte",
            condition_value="2.0",
            is_mandatory=True,
            verification_frequency="per_semester",
        )

        result = await service.add_requirement(program.id, request)

        assert result.program_id == program.id
        assert result.requirement_type == RequirementType.ACADEMIC_GWA
        assert result.condition_operator == "lte"
        assert result.condition_value == "2.0"
        assert result.is_mandatory is True
        assert result.verification_frequency == "per_semester"
        db.add.assert_called_once()
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_add_requirement_to_nonexistent_program(self):
        """Adding a requirement to a nonexistent program should raise ProgramNotFoundError."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        service = ProgramService(db=db)

        request = AddRequirementRequest(
            requirement_type=RequirementType.ENROLLMENT_STATUS,
            description="Must be enrolled",
            condition_operator="eq",
            condition_value="enrolled",
            is_mandatory=True,
            verification_frequency="per_semester",
        )

        with pytest.raises(ProgramNotFoundError):
            await service.add_requirement(uuid.uuid4(), request)

    @pytest.mark.asyncio
    async def test_add_all_requirement_types(self):
        """All requirement types should be storable."""
        program = _make_program()
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        for req_type in RequirementType:
            request = AddRequirementRequest(
                requirement_type=req_type,
                description=f"Test {req_type.value}",
                condition_operator="eq",
                condition_value="test_value",
                is_mandatory=True,
                verification_frequency="once",
            )
            result = await service.add_requirement(program.id, request)
            assert result.requirement_type == req_type


class TestProgramServiceRemoveRequirement:
    """Tests for ProgramService.remove_requirement."""

    @pytest.mark.asyncio
    async def test_remove_existing_requirement(self):
        """Removing an existing requirement should succeed."""
        program = _make_program()
        requirement = _make_requirement(program.id)

        db = AsyncMock()
        # First call returns program (for _get_program_or_raise)
        # Second call returns requirement (for the requirement query)
        mock_program_result = MagicMock()
        mock_program_result.scalar_one_or_none.return_value = program
        mock_req_result = MagicMock()
        mock_req_result.scalar_one_or_none.return_value = requirement
        db.execute = AsyncMock(side_effect=[mock_program_result, mock_req_result])
        db.flush = AsyncMock()
        db.delete = AsyncMock()

        service = ProgramService(db=db)
        await service.remove_requirement(program.id, requirement.id)

        db.delete.assert_awaited_once_with(requirement)
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_requirement(self):
        """Removing a nonexistent requirement should raise ProgramServiceError."""
        program = _make_program()

        db = AsyncMock()
        mock_program_result = MagicMock()
        mock_program_result.scalar_one_or_none.return_value = program
        mock_req_result = MagicMock()
        mock_req_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[mock_program_result, mock_req_result])

        service = ProgramService(db=db)

        with pytest.raises(ProgramServiceError) as exc_info:
            await service.remove_requirement(program.id, uuid.uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_requirement_from_nonexistent_program(self):
        """Removing a requirement from a nonexistent program should raise ProgramNotFoundError."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        service = ProgramService(db=db)

        with pytest.raises(ProgramNotFoundError):
            await service.remove_requirement(uuid.uuid4(), uuid.uuid4())


class TestProgramServiceListRequirements:
    """Tests for ProgramService.list_requirements."""

    @pytest.mark.asyncio
    async def test_list_requirements_returns_all(self):
        """Listing requirements should return all requirements for the program."""
        program = _make_program()
        requirements = [_make_requirement(program.id) for _ in range(3)]

        db = AsyncMock()
        # First call: _get_program_or_raise
        mock_program_result = MagicMock()
        mock_program_result.scalar_one_or_none.return_value = program
        # Second call: list query
        mock_req_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = requirements
        mock_req_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(side_effect=[mock_program_result, mock_req_result])

        service = ProgramService(db=db)
        result = await service.list_requirements(program.id)

        assert len(result) == 3
        for r in result:
            assert r.program_id == program.id

    @pytest.mark.asyncio
    async def test_list_requirements_empty(self):
        """Listing requirements for a program with none should return empty list."""
        program = _make_program()

        db = AsyncMock()
        mock_program_result = MagicMock()
        mock_program_result.scalar_one_or_none.return_value = program
        mock_req_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_req_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(side_effect=[mock_program_result, mock_req_result])

        service = ProgramService(db=db)
        result = await service.list_requirements(program.id)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_requirements_nonexistent_program(self):
        """Listing requirements for a nonexistent program should raise ProgramNotFoundError."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        service = ProgramService(db=db)

        with pytest.raises(ProgramNotFoundError):
            await service.list_requirements(uuid.uuid4())


# ============================================================
# Condition Operator Validation Tests
# ============================================================


class TestConditionOperatorValidation:
    """Tests verifying that condition operator validation works correctly."""

    def test_valid_operators(self):
        """All operators defined in design doc should be accepted."""
        valid_ops = ["lte", "gte", "eq", "neq", "lt", "gt", "contains", "exists", "not_exists"]
        for op in valid_ops:
            request = AddRequirementRequest(
                requirement_type=RequirementType.CUSTOM,
                description="Test",
                condition_operator=op,
                condition_value="test",
                is_mandatory=True,
                verification_frequency="once",
            )
            assert request.condition_operator == op

    def test_invalid_operators_rejected(self):
        """Invalid operators should be rejected with a validation error."""
        invalid_ops = ["between", "in", "like", "not_in", "regex", ""]
        for op in invalid_ops:
            with pytest.raises(Exception):
                AddRequirementRequest(
                    requirement_type=RequirementType.CUSTOM,
                    description="Test",
                    condition_operator=op if op else "x",  # empty handled by min_length
                    condition_value="test",
                    is_mandatory=True,
                    verification_frequency="once",
                )


# ============================================================
# RequirementResponse Schema Tests
# ============================================================


class TestRequirementResponse:
    """Tests for RequirementResponse schema."""

    def test_from_model(self):
        """RequirementResponse should be constructable from a ProgramRequirement model."""
        program_id = uuid.uuid4()
        req = _make_requirement(program_id, RequirementType.DOCUMENT_SUBMISSION)

        response = RequirementResponse.model_validate(req)
        assert response.id == req.id
        assert response.program_id == program_id
        assert response.requirement_type == RequirementType.DOCUMENT_SUBMISSION
        assert response.condition_operator == "lte"
        assert response.is_mandatory is True
