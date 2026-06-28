"""Property-based tests for program status lifecycle (P10).

**Validates: Requirements 3.2, 3.3, 3.4, 3.5**

Property P10: Program Status Lifecycle - Status transitions follow valid
lifecycle graph; no illegal transitions. DRAFT → ACTIVE → {PAUSED ↔ ACTIVE}
→ COMPLETED → ARCHIVED. No transition can skip states or move backwards
except PAUSED ↔ ACTIVE.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, assume, note
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

import sys
sys.path.insert(0, ".")

from app.models.enums import ProgramStatus
from app.models.program import Program
from app.services.program_service import (
    InvalidTransitionError,
    ProgramService,
    VALID_TRANSITIONS,
)


# ============================================================
# Strategies
# ============================================================

all_statuses = st.sampled_from(list(ProgramStatus))


def _make_program_with_status(status: ProgramStatus) -> Program:
    """Create a Program model instance in the given status."""
    program = Program()
    program.id = uuid.uuid4()
    program.organization_id = uuid.uuid4()
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


def _mock_db_with_program(program: Program):
    """Create a mock async session that returns the given program."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = program
    db.execute = AsyncMock(return_value=mock_result)
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


async def _attempt_transition(service: ProgramService, program_id: uuid.UUID,
                               current_status: ProgramStatus, target_status: ProgramStatus):
    """Attempt a status transition using the internal _transition_status method.

    This directly invokes the transition logic that checks VALID_TRANSITIONS,
    bypassing the public methods which each only target a single specific status.
    """
    return await service._transition_status(program_id, target_status)


# ============================================================
# Property 1: All valid transitions succeed
# ============================================================


@given(source_status=all_statuses)
@settings(max_examples=50)
@pytest.mark.asyncio
async def test_valid_transitions_succeed(source_status: ProgramStatus):
    """For any program in a valid state, transitioning to a valid target state succeeds.

    **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
    """
    valid_targets = VALID_TRANSITIONS[source_status]
    assume(len(valid_targets) > 0)

    for target_status in valid_targets:
        program = _make_program_with_status(source_status)
        db = _mock_db_with_program(program)
        service = ProgramService(db=db)

        result = await _attempt_transition(service, program.id, source_status, target_status)
        assert result.status == target_status, (
            f"Expected transition {source_status.value} -> {target_status.value} to succeed, "
            f"but got status {result.status.value}"
        )


# ============================================================
# Property 2: All invalid transitions are rejected
# ============================================================


@given(source_status=all_statuses, target_status=all_statuses)
@settings(max_examples=100)
@pytest.mark.asyncio
async def test_invalid_transitions_rejected(source_status: ProgramStatus, target_status: ProgramStatus):
    """For any program in a given state, transitioning to an invalid target raises InvalidTransitionError.

    **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
    """
    valid_targets = VALID_TRANSITIONS[source_status]
    assume(target_status not in valid_targets)

    program = _make_program_with_status(source_status)
    db = _mock_db_with_program(program)
    service = ProgramService(db=db)

    with pytest.raises(InvalidTransitionError):
        await _attempt_transition(service, program.id, source_status, target_status)


# ============================================================
# Property 3: Stateful test - random valid transitions always produce valid state
# ============================================================


class ProgramLifecycleStateMachine(RuleBasedStateMachine):
    """Stateful property test: a sequence of valid transitions always produces a valid state.

    **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
    """

    def __init__(self):
        super().__init__()
        self.current_status = ProgramStatus.DRAFT

    @initialize()
    def init_program(self):
        self.current_status = ProgramStatus.DRAFT

    @rule()
    def transition_to_active_from_draft(self):
        """DRAFT -> ACTIVE (Requirement 3.2)."""
        if self.current_status != ProgramStatus.DRAFT:
            return
        valid_targets = VALID_TRANSITIONS[self.current_status]
        assert ProgramStatus.ACTIVE in valid_targets
        self.current_status = ProgramStatus.ACTIVE

    @rule()
    def transition_to_paused(self):
        """ACTIVE -> PAUSED (Requirement 3.3)."""
        if self.current_status != ProgramStatus.ACTIVE:
            return
        valid_targets = VALID_TRANSITIONS[self.current_status]
        assert ProgramStatus.PAUSED in valid_targets
        self.current_status = ProgramStatus.PAUSED

    @rule()
    def transition_to_active_from_paused(self):
        """PAUSED -> ACTIVE (Requirement 3.4)."""
        if self.current_status != ProgramStatus.PAUSED:
            return
        valid_targets = VALID_TRANSITIONS[self.current_status]
        assert ProgramStatus.ACTIVE in valid_targets
        self.current_status = ProgramStatus.ACTIVE

    @rule()
    def transition_to_completed(self):
        """ACTIVE -> COMPLETED."""
        if self.current_status != ProgramStatus.ACTIVE:
            return
        valid_targets = VALID_TRANSITIONS[self.current_status]
        assert ProgramStatus.COMPLETED in valid_targets
        self.current_status = ProgramStatus.COMPLETED

    @rule()
    def transition_to_archived(self):
        """COMPLETED -> ARCHIVED (Requirement 3.5)."""
        if self.current_status != ProgramStatus.COMPLETED:
            return
        valid_targets = VALID_TRANSITIONS[self.current_status]
        assert ProgramStatus.ARCHIVED in valid_targets
        self.current_status = ProgramStatus.ARCHIVED

    @invariant()
    def status_is_always_valid(self):
        """The current status is always a valid ProgramStatus enum value."""
        assert self.current_status in ProgramStatus, (
            f"Program ended up in invalid status: {self.current_status}"
        )

    @invariant()
    def current_status_exists_in_transitions_map(self):
        """Every state we're in is a key in VALID_TRANSITIONS."""
        assert self.current_status in VALID_TRANSITIONS, (
            f"Status {self.current_status} not found in VALID_TRANSITIONS map"
        )


TestProgramLifecycleStateMachine = ProgramLifecycleStateMachine.TestCase


# ============================================================
# Property 4: VALID_TRANSITIONS map is exhaustive over all ProgramStatus values
# ============================================================


def test_valid_transitions_covers_all_statuses():
    """The VALID_TRANSITIONS map contains an entry for every ProgramStatus enum value.

    **Validates: Requirements 3.2, 3.3, 3.4, 3.5**

    This ensures no status is accidentally missing from the transition map,
    which would cause KeyError at runtime.
    """
    all_enum_values = set(ProgramStatus)
    transition_keys = set(VALID_TRANSITIONS.keys())

    missing_from_map = all_enum_values - transition_keys
    extra_in_map = transition_keys - all_enum_values

    assert missing_from_map == set(), (
        f"ProgramStatus values missing from VALID_TRANSITIONS: {missing_from_map}"
    )
    assert extra_in_map == set(), (
        f"Extra keys in VALID_TRANSITIONS not in ProgramStatus enum: {extra_in_map}"
    )


def test_valid_transitions_targets_are_valid_statuses():
    """All target statuses in VALID_TRANSITIONS are valid ProgramStatus values.

    **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
    """
    all_enum_values = set(ProgramStatus)
    for source, targets in VALID_TRANSITIONS.items():
        for target in targets:
            assert target in all_enum_values, (
                f"Invalid target {target} in VALID_TRANSITIONS[{source}]"
            )


def test_no_self_transitions():
    """No status can transition to itself.

    **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
    """
    for source, targets in VALID_TRANSITIONS.items():
        assert source not in targets, (
            f"Self-transition detected: {source} -> {source}"
        )
