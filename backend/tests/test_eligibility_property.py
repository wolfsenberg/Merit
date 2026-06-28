"""Property-based tests for eligibility evaluation (P3: Verification Completeness).

**Validates: Requirements 6.2, 6.3**

Property P3: Verification Completeness - ELIGIBLE status implies all mandatory
requirements have passing rule_results. Tests verify the correctness of the
_determine_overall_status logic across all possible input combinations.
"""

import sys
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

sys.path.insert(0, ".")

from app.models.enums import EligibilityStatus
from app.services.compliance_engine import EligibilityService


# ============================================================
# Strategies
# ============================================================

# Boolean flags representing the three inputs to _determine_overall_status
bool_flag = st.booleans()


# ============================================================
# Helper
# ============================================================

def _make_service() -> EligibilityService:
    """Create an EligibilityService instance with a mocked DB (only _determine_overall_status is tested)."""
    return EligibilityService(db=MagicMock())


# ============================================================
# Property 1: ELIGIBLE implies all mandatory passed
# (Requirement 6.2: WHEN all mandatory requirements pass, status is ELIGIBLE)
# ============================================================


@given(
    all_mandatory_passed=bool_flag,
    has_pending=bool_flag,
    any_optional_passed=bool_flag,
)
@settings(max_examples=200)
def test_eligible_implies_all_mandatory_passed(
    all_mandatory_passed: bool,
    has_pending: bool,
    any_optional_passed: bool,
):
    """If _determine_overall_status returns ELIGIBLE, then all_mandatory_passed must be True
    and has_pending must be False.

    **Validates: Requirements 6.2**
    """
    service = _make_service()
    status = service._determine_overall_status(
        all_mandatory_passed=all_mandatory_passed,
        has_pending=has_pending,
        any_optional_passed=any_optional_passed,
    )

    if status == EligibilityStatus.ELIGIBLE:
        assert all_mandatory_passed is True, (
            f"ELIGIBLE status returned but all_mandatory_passed={all_mandatory_passed}. "
            f"Inputs: has_pending={has_pending}, any_optional_passed={any_optional_passed}"
        )
        assert has_pending is False, (
            f"ELIGIBLE status returned but has_pending={has_pending}. "
            f"Inputs: all_mandatory_passed={all_mandatory_passed}, any_optional_passed={any_optional_passed}"
        )


# ============================================================
# Property 2: INELIGIBLE implies at least one mandatory failed
# (Requirement 6.3: WHEN any mandatory requirement fails, status is INELIGIBLE)
# ============================================================


@given(
    all_mandatory_passed=bool_flag,
    has_pending=bool_flag,
    any_optional_passed=bool_flag,
)
@settings(max_examples=200)
def test_ineligible_implies_mandatory_failed(
    all_mandatory_passed: bool,
    has_pending: bool,
    any_optional_passed: bool,
):
    """If _determine_overall_status returns INELIGIBLE, then all_mandatory_passed must be False,
    has_pending must be False, and any_optional_passed must be False.

    **Validates: Requirements 6.3**
    """
    service = _make_service()
    status = service._determine_overall_status(
        all_mandatory_passed=all_mandatory_passed,
        has_pending=has_pending,
        any_optional_passed=any_optional_passed,
    )

    if status == EligibilityStatus.INELIGIBLE:
        assert all_mandatory_passed is False, (
            f"INELIGIBLE status returned but all_mandatory_passed={all_mandatory_passed}. "
            f"Inputs: has_pending={has_pending}, any_optional_passed={any_optional_passed}"
        )
        assert has_pending is False, (
            f"INELIGIBLE status returned but has_pending={has_pending}. "
            f"Mandatory should have explicit failures, not just pending."
        )
        assert any_optional_passed is False, (
            f"INELIGIBLE status returned but any_optional_passed={any_optional_passed}. "
            f"When optional passes, status should be PARTIAL, not INELIGIBLE."
        )


# ============================================================
# Property 3: PENDING_VERIFICATION implies at least one mandatory requirement
# has no verified submission
# ============================================================


@given(
    all_mandatory_passed=bool_flag,
    has_pending=bool_flag,
    any_optional_passed=bool_flag,
)
@settings(max_examples=200)
def test_pending_verification_implies_has_pending(
    all_mandatory_passed: bool,
    has_pending: bool,
    any_optional_passed: bool,
):
    """If _determine_overall_status returns PENDING_VERIFICATION, then has_pending must be True.

    **Validates: Requirements 6.2, 6.3**
    """
    service = _make_service()
    status = service._determine_overall_status(
        all_mandatory_passed=all_mandatory_passed,
        has_pending=has_pending,
        any_optional_passed=any_optional_passed,
    )

    if status == EligibilityStatus.PENDING_VERIFICATION:
        assert has_pending is True, (
            f"PENDING_VERIFICATION status returned but has_pending={has_pending}. "
            f"Inputs: all_mandatory_passed={all_mandatory_passed}, any_optional_passed={any_optional_passed}"
        )


# ============================================================
# Property 4: _determine_overall_status is deterministic
# Same inputs always produce same output
# ============================================================


@given(
    all_mandatory_passed=bool_flag,
    has_pending=bool_flag,
    any_optional_passed=bool_flag,
)
@settings(max_examples=200)
def test_determine_status_is_deterministic(
    all_mandatory_passed: bool,
    has_pending: bool,
    any_optional_passed: bool,
):
    """_determine_overall_status called twice with the same inputs must return
    the same result.

    **Validates: Requirements 6.2, 6.3**
    """
    service = _make_service()
    result1 = service._determine_overall_status(
        all_mandatory_passed=all_mandatory_passed,
        has_pending=has_pending,
        any_optional_passed=any_optional_passed,
    )
    result2 = service._determine_overall_status(
        all_mandatory_passed=all_mandatory_passed,
        has_pending=has_pending,
        any_optional_passed=any_optional_passed,
    )
    assert result1 == result2, (
        f"Non-deterministic result: first={result1}, second={result2}. "
        f"Inputs: all_mandatory_passed={all_mandatory_passed}, "
        f"has_pending={has_pending}, any_optional_passed={any_optional_passed}"
    )


# ============================================================
# Property 5: Status determination covers all possible combinations
# (output is always a valid EligibilityStatus)
# ============================================================


@given(
    all_mandatory_passed=bool_flag,
    has_pending=bool_flag,
    any_optional_passed=bool_flag,
)
@settings(max_examples=200)
def test_status_always_valid_eligibility_status(
    all_mandatory_passed: bool,
    has_pending: bool,
    any_optional_passed: bool,
):
    """For all possible combinations of boolean flags, _determine_overall_status must
    return a valid EligibilityStatus enum member.

    **Validates: Requirements 6.2, 6.3**
    """
    service = _make_service()
    status = service._determine_overall_status(
        all_mandatory_passed=all_mandatory_passed,
        has_pending=has_pending,
        any_optional_passed=any_optional_passed,
    )

    valid_statuses = {
        EligibilityStatus.ELIGIBLE,
        EligibilityStatus.INELIGIBLE,
        EligibilityStatus.PENDING_VERIFICATION,
        EligibilityStatus.PARTIAL,
    }
    assert status in valid_statuses, (
        f"Status {status} is not a valid EligibilityStatus. "
        f"Inputs: all_mandatory_passed={all_mandatory_passed}, "
        f"has_pending={has_pending}, any_optional_passed={any_optional_passed}"
    )
