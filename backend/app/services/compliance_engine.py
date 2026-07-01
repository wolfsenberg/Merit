"""Compliance engine for evaluating recipient eligibility conditions.

This module provides the core condition evaluation logic used by the compliance
engine to determine whether a recipient's actual values satisfy program requirement
conditions. It also provides the EligibilityService for evaluating a recipient's
overall eligibility against all program requirements.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.compliance_submission import ComplianceSubmission
from app.models.eligibility_evaluation import EligibilityEvaluation
from app.models.enums import (
    ApplicationStatus,
    EligibilityStatus,
    VerificationStatus,
)
from app.models.ocr_result import OCRResult
from app.models.program_requirement import ProgramRequirement

# Valid condition operators for requirement evaluation
VALID_OPERATORS = frozenset(
    {"lte", "gte", "eq", "neq", "lt", "gt", "contains", "exists", "not_exists"}
)


def evaluate_condition(
    operator: str, actual_value: Optional[str], condition_value: str
) -> bool:
    """Evaluate a single condition against an actual value.

    Supports numeric and string comparisons with fail-safe behavior.

    Args:
        operator: The comparison operator. Must be one of:
            lte, gte, eq, neq, lt, gt, contains, exists, not_exists
        actual_value: The actual value extracted from OCR/submission.
            May be None for exists/not_exists checks.
        condition_value: The expected/threshold value from the requirement.

    Returns:
        True if the condition is satisfied, False otherwise.
        Returns False on parse errors for numeric comparisons (fail-safe).

    Raises:
        ValueError: If operator is not a valid condition operator.
    """
    if operator not in VALID_OPERATORS:
        raise ValueError(
            f"Invalid operator '{operator}'. "
            f"Must be one of: {', '.join(sorted(VALID_OPERATORS))}"
        )

    # exists: True only if actual_value is not None AND not empty/whitespace
    if operator == "exists":
        return actual_value is not None and actual_value.strip() != ""

    # not_exists: True only if actual_value IS None or empty/whitespace
    if operator == "not_exists":
        return actual_value is None or actual_value.strip() == ""

    # For all other operators, None actual_value means condition fails
    if actual_value is None:
        return False

    # Case-insensitive string equality
    if operator == "eq":
        return actual_value.strip().lower() == condition_value.strip().lower()

    # Case-insensitive string inequality
    if operator == "neq":
        return actual_value.strip().lower() != condition_value.strip().lower()

    # Case-insensitive substring check
    if operator == "contains":
        return condition_value.strip().lower() in actual_value.strip().lower()

    # Numeric comparisons with parse-error fail-safe
    try:
        actual_num = float(actual_value)
        expected_num = float(condition_value)
    except (ValueError, TypeError):
        return False

    if operator == "lte":
        return actual_num <= expected_num
    elif operator == "gte":
        return actual_num >= expected_num
    elif operator == "lt":
        return actual_num < expected_num
    elif operator == "gt":
        return actual_num > expected_num

    # Should never reach here due to the operator validation above
    return False


# Mapping from verification_frequency string to timedelta for scheduling
FREQUENCY_TO_TIMEDELTA: dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "biweekly": timedelta(weeks=2),
    "monthly": timedelta(days=30),
    "per_semester": timedelta(days=180),
    "quarterly": timedelta(days=90),
    "annually": timedelta(days=365),
    "once": timedelta(days=365 * 10),  # effectively no re-evaluation
}


def _parse_frequency(frequency: str) -> timedelta:
    """Parse a verification frequency string into a timedelta.

    Falls back to 30 days if the frequency is not recognized.
    """
    return FREQUENCY_TO_TIMEDELTA.get(frequency.lower(), timedelta(days=30))


def _calculate_next_evaluation_date(
    requirements: list[ProgramRequirement],
) -> datetime:
    """Calculate the next evaluation due date based on the shortest verification frequency.

    Args:
        requirements: List of program requirements.

    Returns:
        The next evaluation due datetime (UTC).
    """
    if not requirements:
        return datetime.now(timezone.utc) + timedelta(days=30)

    shortest = min(_parse_frequency(r.verification_frequency) for r in requirements)
    return datetime.now(timezone.utc) + shortest


def _extract_value_for_requirement(
    structured_data: Optional[dict], requirement: ProgramRequirement
) -> Optional[str]:
    """Extract the relevant value from OCR structured_data for a given requirement.

    Maps requirement_type to expected field names in the structured data.
    Falls back to looking up by requirement type value directly.

    Args:
        structured_data: The OCR-extracted structured data dict.
        requirement: The program requirement being evaluated.

    Returns:
        The extracted value as a string, or None if not found.
    """
    if not structured_data:
        return None

    # Mapping from requirement type to common field names in OCR data
    field_mappings: dict[str, list[str]] = {
        "academic_gwa": ["gwa", "grade", "average", "gpa"],
        "enrollment_status": ["enrollment_status", "status", "enrollment"],
        "document_submission": ["document", "submitted", "file"],
        "milestone_completion": ["milestone", "completion", "progress"],
        "attendance": ["attendance", "attendance_rate", "present"],
        "custom": [],
    }

    req_type = requirement.requirement_type.value
    candidate_fields = field_mappings.get(req_type, [])

    # Try each candidate field name (case-insensitive lookup)
    for field_name in candidate_fields:
        for key, value in structured_data.items():
            if key.lower() == field_name.lower():
                return str(value) if value is not None else None

    # Fallback: try the requirement type value itself as a key
    for key, value in structured_data.items():
        if key.lower() == req_type.lower():
            return str(value) if value is not None else None

    # Last resort: if there's only one value in structured_data, use it
    if len(structured_data) == 1:
        value = next(iter(structured_data.values()))
        return str(value) if value is not None else None

    return None


class EligibilityServiceError(Exception):
    """Base exception for eligibility service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EligibilityService:
    """Service for evaluating recipient eligibility against program requirements.

    Evaluates all program requirements against a recipient's verified submissions,
    determines overall eligibility status, records evaluation results, and supports
    batch evaluation for all recipients in a program.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_eligibility(
        self, recipient_id: uuid.UUID, program_id: uuid.UUID
    ) -> EligibilityEvaluation:
        """Evaluate a recipient's eligibility for a program.

        Fetches all requirements for the program, checks each against the
        recipient's latest verified submission, and determines overall status.

        Args:
            recipient_id: The recipient's user ID.
            program_id: The program ID to evaluate against.

        Returns:
            The created EligibilityEvaluation record.

        Raises:
            EligibilityServiceError: If no requirements exist for the program.
        """
        # Fetch all requirements for the program
        requirements = await self._get_program_requirements(program_id)
        if not requirements:
            raise EligibilityServiceError(
                f"Program {program_id} has no requirements defined",
                status_code=400,
            )

        rule_results: list[dict] = []
        all_mandatory_passed = True
        has_pending = False
        any_optional_passed = False
        latest_submission_id: Optional[uuid.UUID] = None

        for requirement in requirements:
            # Fetch latest verified submission for this requirement
            submission = await self._get_latest_verified_submission(
                recipient_id=recipient_id,
                requirement_id=requirement.id,
                program_id=program_id,
            )

            if submission is None:
                # No verified submission exists
                if requirement.is_mandatory:
                    all_mandatory_passed = False
                    has_pending = True
                rule_results.append(
                    {
                        "requirement_id": str(requirement.id),
                        "requirement_type": requirement.requirement_type.value,
                        "condition": f"{requirement.condition_operator} {requirement.condition_value}",
                        "actual_value": None,
                        "expected_value": requirement.condition_value,
                        "passed": False,
                        "is_mandatory": requirement.is_mandatory,
                        "reason": "No verified submission found",
                    }
                )
                continue

            # Track the latest submission for the evaluation record
            if latest_submission_id is None:
                latest_submission_id = submission.id

            # Get OCR results for this submission
            actual_value = await self._get_actual_value(submission.id, requirement)

            # Evaluate the condition
            passed = evaluate_condition(
                operator=requirement.condition_operator,
                actual_value=actual_value,
                condition_value=requirement.condition_value,
            )

            if not passed and requirement.is_mandatory:
                all_mandatory_passed = False

            if passed and not requirement.is_mandatory:
                any_optional_passed = True

            reason = (
                "Condition met"
                if passed
                else (
                    f"Value {actual_value} does not satisfy "
                    f"{requirement.condition_operator} {requirement.condition_value}"
                )
            )

            rule_results.append(
                {
                    "requirement_id": str(requirement.id),
                    "requirement_type": requirement.requirement_type.value,
                    "condition": f"{requirement.condition_operator} {requirement.condition_value}",
                    "actual_value": actual_value,
                    "expected_value": requirement.condition_value,
                    "passed": passed,
                    "is_mandatory": requirement.is_mandatory,
                    "reason": reason,
                }
            )

        # Determine overall status
        overall_status = self._determine_overall_status(
            all_mandatory_passed=all_mandatory_passed,
            has_pending=has_pending,
            any_optional_passed=any_optional_passed,
        )

        # Calculate next evaluation due date
        next_evaluation_due = _calculate_next_evaluation_date(requirements)

        # If no submission was found at all, we still need a submission_id
        # Use the first available submission for this recipient+program
        if latest_submission_id is None:
            latest_submission_id = await self._get_any_submission_id(
                recipient_id, program_id
            )

        # Record the evaluation
        evaluation = EligibilityEvaluation(
            id=uuid.uuid4(),
            submission_id=latest_submission_id,
            recipient_id=recipient_id,
            program_id=program_id,
            overall_status=overall_status,
            rule_results=rule_results,
            evaluated_at=datetime.now(timezone.utc),
            next_evaluation_due=next_evaluation_due,
        )

        self.db.add(evaluation)
        await self.db.flush()

        return evaluation

    async def evaluate_batch(
        self, program_id: uuid.UUID
    ) -> list[EligibilityEvaluation]:
        """Evaluate all recipients enrolled in a program.

        Finds all recipients with approved applications for the program
        and evaluates each one.

        Args:
            program_id: The program ID to batch-evaluate.

        Returns:
            List of evaluation results for all recipients.
        """
        # Get all recipients with approved applications for this program
        result = await self.db.execute(
            select(Application.recipient_id).where(
                and_(
                    Application.program_id == program_id,
                    Application.status == ApplicationStatus.APPROVED,
                )
            )
        )
        recipient_ids = [row[0] for row in result.all()]

        # Also include PENDING applications (recipients actively enrolled)
        result_pending = await self.db.execute(
            select(Application.recipient_id).where(
                and_(
                    Application.program_id == program_id,
                    Application.status == ApplicationStatus.PENDING,
                )
            )
        )
        pending_ids = [row[0] for row in result_pending.all()]

        all_recipient_ids = list(set(recipient_ids + pending_ids))

        evaluations: list[EligibilityEvaluation] = []
        for recipient_id in all_recipient_ids:
            try:
                evaluation = await self.evaluate_eligibility(recipient_id, program_id)
                evaluations.append(evaluation)
            except EligibilityServiceError:
                # Skip recipients where evaluation fails (e.g., no requirements)
                continue

        return evaluations

    def _determine_overall_status(
        self,
        all_mandatory_passed: bool,
        has_pending: bool,
        any_optional_passed: bool,
    ) -> EligibilityStatus:
        """Determine the overall eligibility status based on rule results.

        Logic:
        - PENDING_VERIFICATION: some mandatory requirements have no verified submission
        - ELIGIBLE: all mandatory requirements pass
        - PARTIAL: mandatory requirements fail but some optional pass
        - INELIGIBLE: mandatory requirements fail and no optional pass

        Args:
            all_mandatory_passed: Whether all mandatory requirements passed.
            has_pending: Whether any mandatory requirements are missing submissions.
            any_optional_passed: Whether any optional requirements passed.

        Returns:
            The determined EligibilityStatus.
        """
        if has_pending:
            return EligibilityStatus.PENDING_VERIFICATION
        elif all_mandatory_passed:
            return EligibilityStatus.ELIGIBLE
        elif any_optional_passed:
            return EligibilityStatus.PARTIAL
        else:
            return EligibilityStatus.INELIGIBLE

    async def _get_program_requirements(
        self, program_id: uuid.UUID
    ) -> list[ProgramRequirement]:
        """Fetch all requirements for a program."""
        result = await self.db.execute(
            select(ProgramRequirement).where(
                ProgramRequirement.program_id == program_id
            )
        )
        return list(result.scalars().all())

    async def _get_latest_verified_submission(
        self,
        recipient_id: uuid.UUID,
        requirement_id: uuid.UUID,
        program_id: uuid.UUID,
    ) -> Optional[ComplianceSubmission]:
        """Fetch the latest verified submission for a recipient and requirement.

        Only submissions with VERIFIED or AUTO_VERIFIED status are considered.
        """
        result = await self.db.execute(
            select(ComplianceSubmission)
            .where(
                and_(
                    ComplianceSubmission.recipient_id == recipient_id,
                    ComplianceSubmission.requirement_id == requirement_id,
                    ComplianceSubmission.program_id == program_id,
                    ComplianceSubmission.status.in_(
                        [VerificationStatus.VERIFIED, VerificationStatus.AUTO_VERIFIED]
                    ),
                )
            )
            .order_by(ComplianceSubmission.submitted_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_actual_value(
        self, submission_id: uuid.UUID, requirement: ProgramRequirement
    ) -> Optional[str]:
        """Get the actual value from OCR results for a submission and requirement."""
        result = await self.db.execute(
            select(OCRResult)
            .where(OCRResult.submission_id == submission_id)
            .order_by(OCRResult.created_at.desc())
            .limit(1)
        )
        ocr_result = result.scalar_one_or_none()

        if ocr_result is None:
            return None

        return _extract_value_for_requirement(
            ocr_result.structured_data, requirement
        )

    async def _get_any_submission_id(
        self, recipient_id: uuid.UUID, program_id: uuid.UUID
    ) -> Optional[uuid.UUID]:
        """Get any submission ID for the recipient and program (fallback)."""
        result = await self.db.execute(
            select(ComplianceSubmission.id)
            .where(
                and_(
                    ComplianceSubmission.recipient_id == recipient_id,
                    ComplianceSubmission.program_id == program_id,
                )
            )
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row if row else None
