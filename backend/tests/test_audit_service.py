"""Unit tests for audit logging service."""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, ".")

from app.schemas.audit import (
    AuditLogListResponse,
    AuditLogQueryParams,
    AuditLogResponse,
)
from app.services.audit_service import AuditService

# ============================================================
# Test fixtures
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
# Schema Validation Tests
# ============================================================


class TestAuditSchemas:
    """Tests for audit Pydantic schemas."""

    def test_audit_log_response_valid(self):
        """A valid audit log response should pass validation."""
        resp = AuditLogResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            action="funds_disbursed",
            resource_type="transaction",
            resource_id=str(uuid.uuid4()),
            details={"amount": 1000.0},
            ip_address="192.168.1.1",
            created_at=datetime.now(timezone.utc),
        )
        assert resp.action == "funds_disbursed"
        assert resp.resource_type == "transaction"

    def test_audit_log_response_optional_fields(self):
        """Audit log should allow None for optional fields."""
        resp = AuditLogResponse(
            id=uuid.uuid4(),
            user_id=None,
            action="system_action",
            resource_type="program",
            resource_id=str(uuid.uuid4()),
            details=None,
            ip_address=None,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.user_id is None
        assert resp.details is None
        assert resp.ip_address is None

    def test_audit_log_list_response(self):
        """AuditLogListResponse should include logs and total count."""
        resp = AuditLogListResponse(logs=[], total=0)
        assert resp.total == 0
        assert resp.logs == []

    def test_audit_log_query_params_defaults(self):
        """AuditLogQueryParams should have sensible defaults."""
        params = AuditLogQueryParams()
        assert params.user_id is None
        assert params.action is None
        assert params.resource_type is None
        assert params.start_time is None
        assert params.end_time is None
        assert params.limit == 50
        assert params.offset == 0

    def test_audit_log_query_params_with_filters(self):
        """AuditLogQueryParams should accept filter values."""
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        params = AuditLogQueryParams(
            user_id=user_id,
            action="compliance_evaluation",
            resource_type="evaluation",
            start_time=now - timedelta(hours=1),
            end_time=now,
            limit=10,
            offset=5,
        )
        assert params.user_id == user_id
        assert params.action == "compliance_evaluation"
        assert params.limit == 10
        assert params.offset == 5


# ============================================================
# create_log Tests
# ============================================================


class TestCreateLog:
    """Tests for AuditService.create_log."""

    @pytest.mark.asyncio
    async def test_create_log_with_all_fields(self, audit_service, mock_db):
        """Should create an audit log entry with all fields populated."""
        user_id = uuid.uuid4()
        resource_id = str(uuid.uuid4())

        result = await audit_service.create_log(
            action="funds_disbursed",
            resource_type="transaction",
            resource_id=resource_id,
            user_id=user_id,
            details={"amount": 500.0, "tx_hash": "abc123"},
            ip_address="10.0.0.1",
        )

        assert result.action == "funds_disbursed"
        assert result.resource_type == "transaction"
        assert result.resource_id == resource_id
        assert result.user_id == user_id
        assert result.details == {"amount": 500.0, "tx_hash": "abc123"}
        assert result.ip_address == "10.0.0.1"
        assert result.created_at is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_log_system_action_no_user(self, audit_service, mock_db):
        """Should allow None user_id for system-initiated actions."""
        resource_id = str(uuid.uuid4())

        result = await audit_service.create_log(
            action="batch_evaluation",
            resource_type="program",
            resource_id=resource_id,
        )

        assert result.user_id is None
        assert result.action == "batch_evaluation"
        assert result.ip_address is None
        assert result.details is None
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_log_compliance_evaluation(self, audit_service, mock_db):
        """Should record compliance evaluation in audit log."""
        user_id = uuid.uuid4()
        eval_id = str(uuid.uuid4())

        result = await audit_service.create_log(
            action="compliance_evaluation",
            resource_type="evaluation",
            resource_id=eval_id,
            user_id=user_id,
            details={"status": "eligible", "results_count": 3},
        )

        assert result.action == "compliance_evaluation"
        assert result.resource_type == "evaluation"
        assert result.details["status"] == "eligible"

    @pytest.mark.asyncio
    async def test_create_log_program_status_change(self, audit_service, mock_db):
        """Should record program status changes in audit log."""
        user_id = uuid.uuid4()
        program_id = str(uuid.uuid4())

        result = await audit_service.create_log(
            action="program_status_changed",
            resource_type="program",
            resource_id=program_id,
            user_id=user_id,
            details={"old_status": "draft", "new_status": "active"},
            ip_address="192.168.1.100",
        )

        assert result.action == "program_status_changed"
        assert result.details["old_status"] == "draft"
        assert result.details["new_status"] == "active"

    @pytest.mark.asyncio
    async def test_create_log_generates_unique_id(self, audit_service, mock_db):
        """Each log entry should have a unique ID."""
        result1 = await audit_service.create_log(
            action="action_1",
            resource_type="type_1",
            resource_id="res-1",
        )
        result2 = await audit_service.create_log(
            action="action_2",
            resource_type="type_2",
            resource_id="res-2",
        )

        assert result1.id != result2.id


# ============================================================
# query_logs Tests
# ============================================================


class TestQueryLogs:
    """Tests for AuditService.query_logs."""

    @pytest.mark.asyncio
    async def test_query_logs_no_filters(self, audit_service, mock_db):
        """Should return all logs when no filters are applied."""
        now = datetime.now(timezone.utc)
        mock_log = MagicMock()
        mock_log.id = uuid.uuid4()
        mock_log.user_id = uuid.uuid4()
        mock_log.action = "funds_disbursed"
        mock_log.resource_type = "transaction"
        mock_log.resource_id = str(uuid.uuid4())
        mock_log.details = {"amount": 100.0}
        mock_log.ip_address = "10.0.0.1"
        mock_log.created_at = now

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock logs query
        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[mock_log])
        )

        mock_db.execute.side_effect = [mock_count_result, mock_logs_result]

        params = AuditLogQueryParams()
        result = await audit_service.query_logs(params)

        assert isinstance(result, AuditLogListResponse)
        assert result.total == 1
        assert len(result.logs) == 1
        assert result.logs[0].action == "funds_disbursed"

    @pytest.mark.asyncio
    async def test_query_logs_with_user_filter(self, audit_service, mock_db):
        """Should filter logs by user_id."""
        user_id = uuid.uuid4()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[])
        )

        mock_db.execute.side_effect = [mock_count_result, mock_logs_result]

        params = AuditLogQueryParams(user_id=user_id)
        result = await audit_service.query_logs(params)

        assert result.total == 0
        assert result.logs == []

    @pytest.mark.asyncio
    async def test_query_logs_with_action_filter(self, audit_service, mock_db):
        """Should filter logs by action type."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[])
        )

        mock_db.execute.side_effect = [mock_count_result, mock_logs_result]

        params = AuditLogQueryParams(action="compliance_evaluation")
        result = await audit_service.query_logs(params)

        assert result.total == 0

    @pytest.mark.asyncio
    async def test_query_logs_with_time_range(self, audit_service, mock_db):
        """Should filter logs by time range."""
        now = datetime.now(timezone.utc)

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[])
        )

        mock_db.execute.side_effect = [mock_count_result, mock_logs_result]

        params = AuditLogQueryParams(
            start_time=now - timedelta(hours=1),
            end_time=now,
        )
        result = await audit_service.query_logs(params)

        assert result.total == 0

    @pytest.mark.asyncio
    async def test_query_logs_with_resource_type_filter(self, audit_service, mock_db):
        """Should filter logs by resource_type."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[])
        )

        mock_db.execute.side_effect = [mock_count_result, mock_logs_result]

        params = AuditLogQueryParams(resource_type="program")
        result = await audit_service.query_logs(params)

        assert result.total == 0

    @pytest.mark.asyncio
    async def test_query_logs_pagination(self, audit_service, mock_db):
        """Should respect limit and offset parameters."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100

        mock_logs_result = MagicMock()
        mock_logs_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[])
        )

        mock_db.execute.side_effect = [mock_count_result, mock_logs_result]

        params = AuditLogQueryParams(limit=10, offset=20)
        result = await audit_service.query_logs(params)

        # Total should reflect the full count regardless of pagination
        assert result.total == 100


# ============================================================
# Append-Only Enforcement Tests
# ============================================================


class TestAppendOnlyEnforcement:
    """Tests verifying that AuditService enforces append-only semantics."""

    def test_no_update_method(self, audit_service):
        """AuditService should not expose any update method."""
        assert not hasattr(audit_service, "update_log")
        assert not hasattr(audit_service, "update")
        assert not hasattr(audit_service, "edit_log")

    def test_no_delete_method(self, audit_service):
        """AuditService should not expose any delete method."""
        assert not hasattr(audit_service, "delete_log")
        assert not hasattr(audit_service, "delete")
        assert not hasattr(audit_service, "remove_log")

    def test_only_create_and_query_methods(self, audit_service):
        """AuditService should only have create_log and query_logs as public methods."""
        public_methods = [
            m for m in dir(audit_service)
            if not m.startswith("_") and callable(getattr(audit_service, m))
        ]
        # Only create_log and query_logs should be public callable methods
        assert "create_log" in public_methods
        assert "query_logs" in public_methods
        # No mutating methods
        for method in public_methods:
            assert "update" not in method.lower()
            assert "delete" not in method.lower()
            assert "remove" not in method.lower()
