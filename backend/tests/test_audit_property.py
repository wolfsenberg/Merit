"""Property-based tests for Audit Trail Completeness (Property P7).

**Validates: Requirements 11.1, 11.2, 11.3, 11.4**

Property P7: Audit Trail Completeness
∀ state-changing operation op: There exists an audit_log entry with
action == op.type, resource_id == op.target_id, and created_at within
1 second of op execution. Every significant action is recorded.
"""

import inspect
import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, ".")

from app.schemas.audit import (
    AuditLogListResponse,
    AuditLogQueryParams,
    AuditLogResponse,
)
from app.services.audit_service import AuditService

# ============================================================
# Strategies
# ============================================================

# Strategy for actions representing state-changing operations
action_strategy = st.sampled_from([
    "funds_disbursed",
    "compliance_evaluation",
    "program_status_changed",
    "program_created",
    "document_verified",
    "document_rejected",
    "user_registered",
    "wallet_created",
    "application_submitted",
    "batch_evaluation",
])

# Strategy for resource types
resource_type_strategy = st.sampled_from([
    "transaction",
    "evaluation",
    "program",
    "document",
    "user",
    "wallet",
    "application",
])

# Strategy for resource IDs (UUID-like strings)
resource_id_strategy = st.builds(lambda: str(uuid.uuid4()))

# Strategy for optional user IDs
user_id_strategy = st.one_of(st.none(), st.builds(uuid.uuid4))

# Strategy for optional IP addresses
ip_address_strategy = st.one_of(
    st.none(),
    st.tuples(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}"),
)

# Strategy for optional details dictionaries
details_strategy = st.one_of(
    st.none(),
    st.fixed_dictionaries({
        "amount": st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
    }),
    st.fixed_dictionaries({
        "status": st.sampled_from(["eligible", "ineligible", "pending"]),
        "results_count": st.integers(min_value=0, max_value=100),
    }),
    st.fixed_dictionaries({
        "old_status": st.sampled_from(["draft", "active", "paused"]),
        "new_status": st.sampled_from(["active", "paused", "completed"]),
    }),
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def audit_service(mock_db):
    """Create an AuditService instance with mocked dependencies."""
    return AuditService(db=mock_db)


# ============================================================
# Property 1: create_log always produces a valid log entry with timestamp
# ============================================================


class TestPropertyP7AuditTrailCompleteness:
    """Property P7: Every state-changing operation produces an audit log entry
    within 1 second.

    **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
    """

    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
        resource_id=resource_id_strategy,
        user_id=user_id_strategy,
        details=details_strategy,
        ip_address=ip_address_strategy,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_create_log_always_produces_valid_entry_with_timestamp(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id,
        details,
        ip_address,
    ):
        """For any action/resource_type/resource_id combination, create_log
        always produces a valid log entry with a timestamp within 1 second of
        the call.

        **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
        """
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        service = AuditService(db=mock_db)

        before = datetime.now(timezone.utc)

        result = await service.create_log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
        )

        after = datetime.now(timezone.utc)

        # The result must be an AuditLogResponse
        assert isinstance(result, AuditLogResponse)

        # All input fields must be faithfully recorded
        assert result.action == action
        assert result.resource_type == resource_type
        assert result.resource_id == resource_id
        assert result.user_id == user_id
        assert result.details == details
        assert result.ip_address == ip_address

        # A valid UUID must be generated
        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

        # Timestamp must be present and within 1 second of the operation
        assert result.created_at is not None
        assert before <= result.created_at <= after
        assert (after - before) <= timedelta(seconds=1)

        # The DB must have been called (entry persisted)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    # ============================================================
    # Property 2: Append-only - no update or delete methods exist
    # ============================================================

    def test_audit_service_has_no_update_methods(self):
        """The AuditService has no update or delete methods, enforcing
        append-only semantics.

        **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
        """
        # Get all public methods of AuditService
        public_methods = [
            name for name, method in inspect.getmembers(AuditService, predicate=inspect.isfunction)
            if not name.startswith("_")
        ]

        # Verify no update/delete/remove/modify methods exist
        forbidden_patterns = ["update", "delete", "remove", "modify", "edit", "purge", "clear"]
        for method_name in public_methods:
            for pattern in forbidden_patterns:
                assert pattern not in method_name.lower(), (
                    f"AuditService has method '{method_name}' which contains "
                    f"forbidden pattern '{pattern}'. Audit logs must be append-only."
                )

        # Only create_log and query_logs should be public methods
        assert "create_log" in public_methods
        assert "query_logs" in public_methods

    # ============================================================
    # Property 3: Query completeness - all created entries are retrievable
    # ============================================================

    @given(
        actions=st.lists(action_strategy, min_size=1, max_size=5),
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_query_logs_returns_all_matching_entries(
        self,
        actions: list,
        resource_type: str,
    ):
        """For any set of log entries created with the same resource_type,
        query_logs with a matching resource_type filter returns them all.

        **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
        """
        # Create a mock DB that stores entries and returns them on query
        stored_logs = []

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        service = AuditService(db=mock_db)

        # Create log entries
        for action in actions:
            resource_id = str(uuid.uuid4())
            result = await service.create_log(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
            )
            stored_logs.append(result)

        # Now verify query_logs can find them when mock DB returns them
        # Setup mock DB to return the stored logs for query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = len(stored_logs)

        mock_log_objects = []
        for log in stored_logs:
            mock_obj = MagicMock()
            mock_obj.id = log.id
            mock_obj.user_id = log.user_id
            mock_obj.action = log.action
            mock_obj.resource_type = log.resource_type
            mock_obj.resource_id = log.resource_id
            mock_obj.details = log.details
            mock_obj.ip_address = log.ip_address
            mock_obj.created_at = log.created_at
            mock_log_objects.append(mock_obj)

        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=mock_log_objects)
        )

        mock_db.execute.side_effect = [mock_count_result, mock_logs_result]

        params = AuditLogQueryParams(resource_type=resource_type)
        query_result = await service.query_logs(params)

        # All entries should be returned
        assert isinstance(query_result, AuditLogListResponse)
        assert query_result.total == len(stored_logs)
        assert len(query_result.logs) == len(stored_logs)

        # Verify all original actions are present in the response
        returned_actions = {log.action for log in query_result.logs}
        for action in actions:
            assert action in returned_actions

        # Verify all returned entries have the correct resource_type
        for log in query_result.logs:
            assert log.resource_type == resource_type

    # ============================================================
    # Property 4: Determinism - same inputs produce matching fields
    # ============================================================

    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
        resource_id=resource_id_strategy,
        user_id=user_id_strategy,
        details=details_strategy,
        ip_address=ip_address_strategy,
    )
    @settings(max_examples=200, deadline=None)
    @pytest.mark.asyncio
    async def test_create_log_is_deterministic_on_input_fields(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id,
        details,
        ip_address,
    ):
        """The audit log is deterministic: same inputs always produce entries
        with matching fields (id and created_at may differ).

        **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
        """
        mock_db1 = AsyncMock()
        mock_db1.add = MagicMock()
        mock_db1.flush = AsyncMock()
        service1 = AuditService(db=mock_db1)

        mock_db2 = AsyncMock()
        mock_db2.add = MagicMock()
        mock_db2.flush = AsyncMock()
        service2 = AuditService(db=mock_db2)

        result1 = await service1.create_log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
        )

        result2 = await service2.create_log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
        )

        # Core fields must be identical
        assert result1.action == result2.action
        assert result1.resource_type == result2.resource_type
        assert result1.resource_id == result2.resource_id
        assert result1.user_id == result2.user_id
        assert result1.details == result2.details
        assert result1.ip_address == result2.ip_address

        # IDs should differ (each entry gets a unique ID)
        assert result1.id != result2.id

        # Timestamps should be close but may differ slightly
        assert abs((result1.created_at - result2.created_at).total_seconds()) < 1.0
