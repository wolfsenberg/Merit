"""Unit tests for eligibility evaluation algorithm.

Tests cover:
- ELIGIBLE when all mandatory requirements pass (Req 6.2)
- INELIGIBLE when any mandatory requirement fails (Req 6.3)
- PENDING_VERIFICATION when submissions are missing (Req 6.4)
- PARTIAL when optional pass but mandatory fail (Req 6.5)
- Evaluation recording with timestamp and next_evaluation_due (Req 6.11)
- Batch evaluation for all recipients in a program (Req 6.12)
- Value extraction from OCR structured_data (Req 6.1)
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.models.application import Application
from app.models.compliance_submission import ComplianceSubmission
from app.models.eligibility_evaluation import EligibilityEvaluation
from app.models.enums import (
    ApplicationStatus,
    EligibilityStatus,
    RequirementType,
    VerificationStatus,
)
from app.models.ocr_result import OCRResult
from app.models.program_requirement import ProgramRequirement
from app.services.compliance_engine import (
    EligibilityService,
    EligibilityServiceError,
    _calculate_next_evaluation_date,
    _extract_value_for_requirement,
    _parse_frequency,
)


# ============================================================
# Helper Factories
# ============================================================


def make_requirement(
    requirement_type=RequirementType.ACADEMIC_GWA,
    condition_operator="lte",
    condition_value="2.0",
    is_mandatory=True,
    verification_frequency="per_semester",
    program_id=None,
    req_id=None,
):
    """Create a mock ProgramRequirement."""
    req = MagicMock(spec=ProgramRequirement)
    req.id = req_id or uuid.uuid4()
    req.program_id = program_id or uuid.uuid4()
    req.requirement_type = requirement_type
    req.condition_operator = condition_operator
    req.condition_value = condition_value
    req.is_mandatory = is_mandatory
    req.verification_frequency = verification_frequency
    return req


def make_submission(
    submission_id=None,
    recipient_id=None,
    requirement_id=None,
    program_id=None,
    status=VerificationStatus.VERIFIED,
):
    """Create a mock ComplianceSubmission."""
    sub = MagicMock(spec=ComplianceSubmission)
    sub.id = submission_id or uuid.uuid4()
    sub.recipient_id = recipient_id or uuid.uuid4()
    sub.requirement_id = requirement_id or uuid.uuid4()
    sub.program_id = program_id or uuid.uuid4()
    sub.status = status
    sub.submitted_at = datetime.now(timezone.utc)
    return sub


def make_ocr_result(structured_data=None, submission_id=None):
    """Create a mock OCRResult."""
    ocr = MagicMock(spec=OCRResult)
    ocr.id = uuid.uuid4()
    ocr.submission_id = submission_id or uuid.uuid4()
    ocr.structured_data = structured_data or {}
    ocr.confidence_score = 0.95
    ocr.created_at = datetime.now(timezone.utc)
    return ocr


# ============================================================
# Tests for _parse_frequency
# ============================================================


class TestParseFrequency:
    """Tests for verification frequency parsing."""

    def test_daily(self):
        assert _parse_frequency("daily") == timedelta(days=1)

    def test_weekly(self):
        assert _parse_frequency("weekly") == timedelta(weeks=1)

    def test_monthly(self):
        assert _parse_frequency("monthly") == timedelta(days=30)

    def test_per_semester(self):
        assert _parse_frequency("per_semester") == timedelta(days=180)

    def test_once(self):
        assert _parse_frequency("once") == timedelta(days=365 * 10)

    def test_unknown_defaults_to_30_days(self):
        assert _parse_frequency("unknown_freq") == timedelta(days=30)

    def test_case_insensitive(self):
        assert _parse_frequency("Monthly") == timedelta(days=30)
        assert _parse_frequency("DAILY") == timedelta(days=1)


# ============================================================
# Tests for _calculate_next_evaluation_date
# ============================================================


class TestCalculateNextEvaluationDate:
    """Tests for next evaluation date calculation."""

    def test_uses_shortest_frequency(self):
        """Should use the shortest verification frequency among requirements."""
        req_daily = make_requirement(verification_frequency="daily")
        req_monthly = make_requirement(verification_frequency="monthly")

        result = _calculate_next_evaluation_date([req_daily, req_monthly])
        # Should be approximately 1 day from now
        expected_min = datetime.now(timezone.utc) + timedelta(hours=23)
        expected_max = datetime.now(timezone.utc) + timedelta(days=1, hours=1)
        assert expected_min <= result <= expected_max

    def test_empty_requirements_defaults_30_days(self):
        """Empty requirements list should default to 30 days."""
        result = _calculate_next_evaluation_date([])
        expected_min = datetime.now(timezone.utc) + timedelta(days=29)
        expected_max = datetime.now(timezone.utc) + timedelta(days=31)
        assert expected_min <= result <= expected_max

    def test_single_requirement(self):
        """Single requirement should use its frequency."""
        req = make_requirement(verification_frequency="weekly")
        result = _calculate_next_evaluation_date([req])
        expected_min = datetime.now(timezone.utc) + timedelta(days=6)
        expected_max = datetime.now(timezone.utc) + timedelta(days=8)
        assert expected_min <= result <= expected_max


# ============================================================
# Tests for _extract_value_for_requirement
# ============================================================


class TestExtractValueForRequirement:
    """Tests for extracting values from OCR structured data."""

    def test_extracts_gwa_field(self):
        """Should extract GWA from structured data."""
        req = make_requirement(requirement_type=RequirementType.ACADEMIC_GWA)
        data = {"gwa": "1.75", "student_id": "2023-001"}
        assert _extract_value_for_requirement(data, req) == "1.75"

    def test_extracts_enrollment_status(self):
        """Should extract enrollment status."""
        req = make_requirement(requirement_type=RequirementType.ENROLLMENT_STATUS)
        data = {"enrollment_status": "enrolled", "year": "3"}
        assert _extract_value_for_requirement(data, req) == "enrolled"

    def test_case_insensitive_field_lookup(self):
        """Should find fields case-insensitively."""
        req = make_requirement(requirement_type=RequirementType.ACADEMIC_GWA)
        data = {"GWA": "1.5"}
        assert _extract_value_for_requirement(data, req) == "1.5"

    def test_returns_none_for_empty_data(self):
        """Should return None when structured data is empty."""
        req = make_requirement(requirement_type=RequirementType.ACADEMIC_GWA)
        assert _extract_value_for_requirement({}, req) is None

    def test_returns_none_for_none_data(self):
        """Should return None when structured data is None."""
        req = make_requirement(requirement_type=RequirementType.ACADEMIC_GWA)
        assert _extract_value_for_requirement(None, req) is None

    def test_fallback_to_single_value(self):
        """Should use single value if only one field exists."""
        req = make_requirement(requirement_type=RequirementType.CUSTOM)
        data = {"some_field": "42"}
        assert _extract_value_for_requirement(data, req) == "42"

    def test_none_value_in_data_returns_none(self):
        """Should return None when the matching field value is None."""
        req = make_requirement(requirement_type=RequirementType.ACADEMIC_GWA)
        data = {"gwa": None}
        assert _extract_value_for_requirement(data, req) is None

    def test_alternative_field_names(self):
        """Should try alternative field names for a requirement type."""
        req = make_requirement(requirement_type=RequirementType.ACADEMIC_GWA)
        data = {"grade": "1.25", "other": "foo"}
        assert _extract_value_for_requirement(data, req) == "1.25"


# ============================================================
# Tests for EligibilityService._determine_overall_status
# ============================================================


class TestDetermineOverallStatus:
    """Tests for overall status determination logic."""

    def setup_method(self):
        self.service = EligibilityService(db=MagicMock())

    def test_eligible_when_all_mandatory_pass(self):
        """ELIGIBLE when all mandatory requirements pass."""
        status = self.service._determine_overall_status(
            all_mandatory_passed=True,
            has_pending=False,
            any_optional_passed=False,
        )
        assert status == EligibilityStatus.ELIGIBLE

    def test_eligible_with_optional_also_passing(self):
        """ELIGIBLE when all mandatory pass and optional also pass."""
        status = self.service._determine_overall_status(
            all_mandatory_passed=True,
            has_pending=False,
            any_optional_passed=True,
        )
        assert status == EligibilityStatus.ELIGIBLE

    def test_ineligible_when_mandatory_fails(self):
        """INELIGIBLE when mandatory requirement fails and no optional pass."""
        status = self.service._determine_overall_status(
            all_mandatory_passed=False,
            has_pending=False,
            any_optional_passed=False,
        )
        assert status == EligibilityStatus.INELIGIBLE

    def test_partial_when_optional_pass_mandatory_fail(self):
        """PARTIAL when optional pass but mandatory fail."""
        status = self.service._determine_overall_status(
            all_mandatory_passed=False,
            has_pending=False,
            any_optional_passed=True,
        )
        assert status == EligibilityStatus.PARTIAL

    def test_pending_verification_when_submissions_missing(self):
        """PENDING_VERIFICATION when some mandatory requirements lack submissions."""
        status = self.service._determine_overall_status(
            all_mandatory_passed=False,
            has_pending=True,
            any_optional_passed=False,
        )
        assert status == EligibilityStatus.PENDING_VERIFICATION

    def test_pending_takes_priority_over_partial(self):
        """PENDING_VERIFICATION takes priority even if some optional pass."""
        status = self.service._determine_overall_status(
            all_mandatory_passed=False,
            has_pending=True,
            any_optional_passed=True,
        )
        assert status == EligibilityStatus.PENDING_VERIFICATION


# ============================================================
# Tests for EligibilityService.evaluate_eligibility (integration with mock DB)
# ============================================================


class TestEvaluateEligibility:
    """Tests for the main evaluate_eligibility method using mocked DB."""

    def setup_method(self):
        self.db = AsyncMock()
        self.service = EligibilityService(db=self.db)
        self.recipient_id = uuid.uuid4()
        self.program_id = uuid.uuid4()

    @pytest.mark.asyncio
    async def test_raises_error_when_no_requirements(self):
        """Should raise error when program has no requirements."""
        # Mock empty requirements
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        self.db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(EligibilityServiceError, match="no requirements"):
            await self.service.evaluate_eligibility(
                self.recipient_id, self.program_id
            )

    @pytest.mark.asyncio
    async def test_eligible_when_all_mandatory_pass(self):
        """Should return ELIGIBLE when all mandatory requirements pass."""
        req = make_requirement(
            program_id=self.program_id,
            condition_operator="lte",
            condition_value="2.0",
            is_mandatory=True,
        )
        submission = make_submission(
            recipient_id=self.recipient_id,
            requirement_id=req.id,
            program_id=self.program_id,
        )
        ocr = make_ocr_result(structured_data={"gwa": "1.5"}, submission_id=submission.id)

        # Mock DB calls in sequence
        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                # _get_program_requirements
                mock_result.scalars.return_value.all.return_value = [req]
            elif call_count[0] == 2:
                # _get_latest_verified_submission
                mock_result.scalar_one_or_none.return_value = submission
            elif call_count[0] == 3:
                # _get_actual_value (OCR result)
                mock_result.scalar_one_or_none.return_value = ocr
            else:
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        self.db.execute = mock_execute
        self.db.add = MagicMock()
        self.db.flush = AsyncMock()

        evaluation = await self.service.evaluate_eligibility(
            self.recipient_id, self.program_id
        )

        assert evaluation.overall_status == EligibilityStatus.ELIGIBLE
        assert evaluation.recipient_id == self.recipient_id
        assert evaluation.program_id == self.program_id
        assert evaluation.rule_results is not None
        assert len(evaluation.rule_results) == 1
        assert evaluation.rule_results[0]["passed"] is True
        assert evaluation.next_evaluation_due is not None
        assert evaluation.evaluated_at is not None

    @pytest.mark.asyncio
    async def test_ineligible_when_mandatory_fails(self):
        """Should return INELIGIBLE when mandatory requirement fails."""
        req = make_requirement(
            program_id=self.program_id,
            condition_operator="lte",
            condition_value="2.0",
            is_mandatory=True,
        )
        submission = make_submission(
            recipient_id=self.recipient_id,
            requirement_id=req.id,
            program_id=self.program_id,
        )
        # GWA 3.0 fails the lte 2.0 condition
        ocr = make_ocr_result(structured_data={"gwa": "3.0"}, submission_id=submission.id)

        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.scalars.return_value.all.return_value = [req]
            elif call_count[0] == 2:
                mock_result.scalar_one_or_none.return_value = submission
            elif call_count[0] == 3:
                mock_result.scalar_one_or_none.return_value = ocr
            else:
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        self.db.execute = mock_execute
        self.db.add = MagicMock()
        self.db.flush = AsyncMock()

        evaluation = await self.service.evaluate_eligibility(
            self.recipient_id, self.program_id
        )

        assert evaluation.overall_status == EligibilityStatus.INELIGIBLE
        assert evaluation.rule_results[0]["passed"] is False

    @pytest.mark.asyncio
    async def test_pending_verification_when_no_submission(self):
        """Should return PENDING_VERIFICATION when mandatory requirement has no submission."""
        req = make_requirement(
            program_id=self.program_id,
            is_mandatory=True,
        )

        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.scalars.return_value.all.return_value = [req]
            elif call_count[0] == 2:
                # No verified submission
                mock_result.scalar_one_or_none.return_value = None
            elif call_count[0] == 3:
                # _get_any_submission_id fallback
                mock_result.scalar_one_or_none.return_value = uuid.uuid4()
            else:
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        self.db.execute = mock_execute
        self.db.add = MagicMock()
        self.db.flush = AsyncMock()

        evaluation = await self.service.evaluate_eligibility(
            self.recipient_id, self.program_id
        )

        assert evaluation.overall_status == EligibilityStatus.PENDING_VERIFICATION
        assert evaluation.rule_results[0]["reason"] == "No verified submission found"

    @pytest.mark.asyncio
    async def test_partial_when_optional_pass_mandatory_fail(self):
        """Should return PARTIAL when optional passes but mandatory fails."""
        mandatory_req = make_requirement(
            program_id=self.program_id,
            requirement_type=RequirementType.ACADEMIC_GWA,
            condition_operator="lte",
            condition_value="2.0",
            is_mandatory=True,
        )
        optional_req = make_requirement(
            program_id=self.program_id,
            requirement_type=RequirementType.ATTENDANCE,
            condition_operator="gte",
            condition_value="80",
            is_mandatory=False,
        )

        mandatory_sub = make_submission(
            recipient_id=self.recipient_id,
            requirement_id=mandatory_req.id,
            program_id=self.program_id,
        )
        optional_sub = make_submission(
            recipient_id=self.recipient_id,
            requirement_id=optional_req.id,
            program_id=self.program_id,
        )

        # GWA 3.0 fails lte 2.0; attendance 90 passes gte 80
        mandatory_ocr = make_ocr_result(
            structured_data={"gwa": "3.0"}, submission_id=mandatory_sub.id
        )
        optional_ocr = make_ocr_result(
            structured_data={"attendance": "90"}, submission_id=optional_sub.id
        )

        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                # requirements
                mock_result.scalars.return_value.all.return_value = [
                    mandatory_req,
                    optional_req,
                ]
            elif call_count[0] == 2:
                # mandatory submission
                mock_result.scalar_one_or_none.return_value = mandatory_sub
            elif call_count[0] == 3:
                # mandatory OCR
                mock_result.scalar_one_or_none.return_value = mandatory_ocr
            elif call_count[0] == 4:
                # optional submission
                mock_result.scalar_one_or_none.return_value = optional_sub
            elif call_count[0] == 5:
                # optional OCR
                mock_result.scalar_one_or_none.return_value = optional_ocr
            else:
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        self.db.execute = mock_execute
        self.db.add = MagicMock()
        self.db.flush = AsyncMock()

        evaluation = await self.service.evaluate_eligibility(
            self.recipient_id, self.program_id
        )

        assert evaluation.overall_status == EligibilityStatus.PARTIAL
        assert len(evaluation.rule_results) == 2
        # Mandatory failed
        assert evaluation.rule_results[0]["passed"] is False
        assert evaluation.rule_results[0]["is_mandatory"] is True
        # Optional passed
        assert evaluation.rule_results[1]["passed"] is True
        assert evaluation.rule_results[1]["is_mandatory"] is False

    @pytest.mark.asyncio
    async def test_evaluation_records_timestamp(self):
        """Should record evaluation with a timestamp."""
        req = make_requirement(program_id=self.program_id, is_mandatory=True)
        submission = make_submission(
            recipient_id=self.recipient_id,
            requirement_id=req.id,
            program_id=self.program_id,
        )
        ocr = make_ocr_result(structured_data={"gwa": "1.5"}, submission_id=submission.id)

        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.scalars.return_value.all.return_value = [req]
            elif call_count[0] == 2:
                mock_result.scalar_one_or_none.return_value = submission
            elif call_count[0] == 3:
                mock_result.scalar_one_or_none.return_value = ocr
            else:
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        self.db.execute = mock_execute
        self.db.add = MagicMock()
        self.db.flush = AsyncMock()

        before = datetime.now(timezone.utc)
        evaluation = await self.service.evaluate_eligibility(
            self.recipient_id, self.program_id
        )
        after = datetime.now(timezone.utc)

        assert before <= evaluation.evaluated_at <= after

    @pytest.mark.asyncio
    async def test_evaluation_schedules_next_evaluation(self):
        """Should calculate next_evaluation_due based on shortest frequency."""
        req = make_requirement(
            program_id=self.program_id,
            verification_frequency="weekly",
            is_mandatory=True,
        )
        submission = make_submission(
            recipient_id=self.recipient_id,
            requirement_id=req.id,
            program_id=self.program_id,
        )
        ocr = make_ocr_result(structured_data={"gwa": "1.5"}, submission_id=submission.id)

        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.scalars.return_value.all.return_value = [req]
            elif call_count[0] == 2:
                mock_result.scalar_one_or_none.return_value = submission
            elif call_count[0] == 3:
                mock_result.scalar_one_or_none.return_value = ocr
            else:
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        self.db.execute = mock_execute
        self.db.add = MagicMock()
        self.db.flush = AsyncMock()

        evaluation = await self.service.evaluate_eligibility(
            self.recipient_id, self.program_id
        )

        # Weekly = 7 days
        expected_min = datetime.now(timezone.utc) + timedelta(days=6)
        expected_max = datetime.now(timezone.utc) + timedelta(days=8)
        assert expected_min <= evaluation.next_evaluation_due <= expected_max


# ============================================================
# Tests for EligibilityService.evaluate_batch
# ============================================================


class TestEvaluateBatch:
    """Tests for batch evaluation of all recipients in a program."""

    def setup_method(self):
        self.db = AsyncMock()
        self.service = EligibilityService(db=self.db)
        self.program_id = uuid.uuid4()

    @pytest.mark.asyncio
    async def test_batch_evaluates_all_recipients(self):
        """Should evaluate all recipients with approved/pending applications."""
        recipient_1 = uuid.uuid4()
        recipient_2 = uuid.uuid4()

        req = make_requirement(
            program_id=self.program_id,
            is_mandatory=True,
        )

        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                # Approved applications
                mock_result.all.return_value = [(recipient_1,)]
            elif call_count[0] == 2:
                # Pending applications
                mock_result.all.return_value = [(recipient_2,)]
            elif call_count[0] in (3, 6):
                # requirements for each recipient
                mock_result.scalars.return_value.all.return_value = [req]
            elif call_count[0] in (4, 7):
                # No verified submission for either
                mock_result.scalar_one_or_none.return_value = None
            elif call_count[0] in (5, 8):
                # fallback submission_id
                mock_result.scalar_one_or_none.return_value = uuid.uuid4()
            else:
                mock_result.scalar_one_or_none.return_value = None
                mock_result.scalars.return_value.all.return_value = []
                mock_result.all.return_value = []
            return mock_result

        self.db.execute = mock_execute
        self.db.add = MagicMock()
        self.db.flush = AsyncMock()

        evaluations = await self.service.evaluate_batch(self.program_id)

        assert len(evaluations) == 2
        # Both should be PENDING_VERIFICATION since no submissions
        for ev in evaluations:
            assert ev.overall_status == EligibilityStatus.PENDING_VERIFICATION

    @pytest.mark.asyncio
    async def test_batch_with_no_recipients_returns_empty(self):
        """Should return empty list when no recipients are enrolled."""
        call_count = [0]

        async def mock_execute(query, *args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            mock_result.all.return_value = []
            return mock_result

        self.db.execute = mock_execute

        evaluations = await self.service.evaluate_batch(self.program_id)
        assert evaluations == []
