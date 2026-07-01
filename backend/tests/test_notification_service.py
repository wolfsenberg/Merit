"""Unit tests for notification service."""

import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, ".")

from app.models.enums import NotificationType
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationService,
    NotificationServiceError,
)

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
def notification_service(mock_db):
    """Create a NotificationService instance with mocked dependencies."""
    return NotificationService(db=mock_db)


# ============================================================
# Schema Validation Tests
# ============================================================


class TestNotificationSchemas:
    """Tests for notification Pydantic schemas."""

    def test_notification_response_valid(self):
        """A valid notification response should pass validation."""
        resp = NotificationResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            notification_type=NotificationType.DOCUMENT_VERIFIED,
            title="Document Verified",
            message="Your document has been verified.",
            payload={"document_id": "abc123"},
            is_read=False,
            created_at=datetime.now(timezone.utc),
            read_at=None,
        )
        assert resp.is_read is False
        assert resp.notification_type == NotificationType.DOCUMENT_VERIFIED

    def test_notification_list_response(self):
        """NotificationListResponse should include total and unread count."""
        resp = NotificationListResponse(
            notifications=[],
            total=0,
            unread_count=0,
        )
        assert resp.total == 0
        assert resp.unread_count == 0

    def test_unread_count_response(self):
        """UnreadCountResponse should hold a count."""
        resp = UnreadCountResponse(unread_count=5)
        assert resp.unread_count == 5


# ============================================================
# send_notification Tests
# ============================================================


class TestSendNotification:
    """Tests for NotificationService.send_notification."""

    @pytest.mark.asyncio
    async def test_send_notification_with_defaults(self, notification_service, mock_db):
        """Should create a notification with default title and message templates."""
        user_id = uuid.uuid4()

        result = await notification_service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.DOCUMENT_VERIFIED,
            payload={"document_id": "doc-123"},
        )

        assert result.user_id == user_id
        assert result.notification_type == NotificationType.DOCUMENT_VERIFIED
        assert result.title == "Document Verified"
        assert result.message == "Your document has been verified successfully."
        assert result.payload == {"document_id": "doc-123"}
        assert result.is_read is False
        assert result.read_at is None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_with_custom_title_and_message(
        self, notification_service, mock_db
    ):
        """Should use custom title and message when provided."""
        user_id = uuid.uuid4()

        result = await notification_service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.FUNDS_RELEASED,
            payload={"amount": 1000.0, "tx_hash": "abc123"},
            title="Custom Title",
            message="Custom message body.",
        )

        assert result.title == "Custom Title"
        assert result.message == "Custom message body."
        assert result.notification_type == NotificationType.FUNDS_RELEASED

    @pytest.mark.asyncio
    async def test_send_notification_eligibility_determined(
        self, notification_service, mock_db
    ):
        """Should create notification for eligibility determination."""
        user_id = uuid.uuid4()

        result = await notification_service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.ELIGIBILITY_DETERMINED,
            payload={"status": "eligible", "program_name": "Test Program"},
        )

        assert result.notification_type == NotificationType.ELIGIBILITY_DETERMINED
        assert result.title == "Eligibility Determined"
        assert result.payload["status"] == "eligible"

    @pytest.mark.asyncio
    async def test_send_notification_manual_review_required(
        self, notification_service, mock_db
    ):
        """Should create notification for manual review required."""
        user_id = uuid.uuid4()

        result = await notification_service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.MANUAL_REVIEW_REQUIRED,
            payload={"document_id": "doc-456", "confidence": 0.65},
        )

        assert result.notification_type == NotificationType.MANUAL_REVIEW_REQUIRED
        assert result.title == "Manual Review Required"

    @pytest.mark.asyncio
    async def test_send_notification_without_payload(self, notification_service, mock_db):
        """Should handle None payload gracefully."""
        user_id = uuid.uuid4()

        result = await notification_service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PROGRAM_UPDATE,
        )

        assert result.payload is None
        assert result.notification_type == NotificationType.PROGRAM_UPDATE


# ============================================================
# get_notifications Tests
# ============================================================


class TestGetNotifications:
    """Tests for NotificationService.get_notifications."""

    @pytest.mark.asyncio
    async def test_get_notifications_returns_list(self, notification_service, mock_db):
        """Should return a list of notifications with total and unread counts."""
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        mock_notification = MagicMock()
        mock_notification.id = uuid.uuid4()
        mock_notification.user_id = user_id
        mock_notification.notification_type = NotificationType.DOCUMENT_VERIFIED
        mock_notification.title = "Document Verified"
        mock_notification.message = "Your document has been verified."
        mock_notification.payload = None
        mock_notification.is_read = False
        mock_notification.created_at = now
        mock_notification.read_at = None

        # Mock total count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock unread count
        mock_unread_result = MagicMock()
        mock_unread_result.scalar.return_value = 1

        # Mock notifications query
        mock_notifications_result = MagicMock()
        mock_notifications_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[mock_notification])
        )

        mock_db.execute.side_effect = [
            mock_count_result,
            mock_unread_result,
            mock_notifications_result,
        ]

        result = await notification_service.get_notifications(user_id=user_id)

        assert isinstance(result, NotificationListResponse)
        assert result.total == 1
        assert result.unread_count == 1
        assert len(result.notifications) == 1
        assert result.notifications[0].title == "Document Verified"

    @pytest.mark.asyncio
    async def test_get_notifications_unread_only(self, notification_service, mock_db):
        """Should filter to only unread notifications when unread_only=True."""
        user_id = uuid.uuid4()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_unread_result = MagicMock()
        mock_unread_result.scalar.return_value = 0

        mock_notifications_result = MagicMock()
        mock_notifications_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[])
        )

        mock_db.execute.side_effect = [
            mock_count_result,
            mock_unread_result,
            mock_notifications_result,
        ]

        result = await notification_service.get_notifications(
            user_id=user_id, unread_only=True
        )

        assert result.total == 0
        assert result.notifications == []

    @pytest.mark.asyncio
    async def test_get_notifications_empty(self, notification_service, mock_db):
        """Should return empty list when user has no notifications."""
        user_id = uuid.uuid4()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_unread_result = MagicMock()
        mock_unread_result.scalar.return_value = 0

        mock_notifications_result = MagicMock()
        mock_notifications_result.scalars.return_value = MagicMock(
            all=MagicMock(return_value=[])
        )

        mock_db.execute.side_effect = [
            mock_count_result,
            mock_unread_result,
            mock_notifications_result,
        ]

        result = await notification_service.get_notifications(user_id=user_id)

        assert result.total == 0
        assert result.unread_count == 0
        assert result.notifications == []


# ============================================================
# mark_as_read Tests
# ============================================================


class TestMarkAsRead:
    """Tests for NotificationService.mark_as_read."""

    @pytest.mark.asyncio
    async def test_mark_as_read_success(self, notification_service, mock_db):
        """Should mark a notification as read and set read_at timestamp."""
        user_id = uuid.uuid4()
        notification_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        mock_notification = MagicMock()
        mock_notification.id = notification_id
        mock_notification.user_id = user_id
        mock_notification.notification_type = NotificationType.FUNDS_RELEASED
        mock_notification.title = "Funds Released"
        mock_notification.message = "Funds have been released."
        mock_notification.payload = {"amount": 500.0}
        mock_notification.is_read = False
        mock_notification.created_at = now
        mock_notification.read_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification
        mock_db.execute.return_value = mock_result

        await notification_service.mark_as_read(
            notification_id=notification_id, user_id=user_id
        )

        assert mock_notification.is_read is True
        assert mock_notification.read_at is not None
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, notification_service, mock_db):
        """Should raise NotificationNotFoundError when notification doesn't exist."""
        user_id = uuid.uuid4()
        notification_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotificationNotFoundError):
            await notification_service.mark_as_read(
                notification_id=notification_id, user_id=user_id
            )

    @pytest.mark.asyncio
    async def test_mark_as_read_wrong_user(self, notification_service, mock_db):
        """Should raise NotificationNotFoundError when notification belongs to different user."""
        user_id = uuid.uuid4()
        notification_id = uuid.uuid4()

        # The query filters by both notification_id AND user_id, so wrong user returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotificationNotFoundError):
            await notification_service.mark_as_read(
                notification_id=notification_id, user_id=user_id
            )


# ============================================================
# get_unread_count Tests
# ============================================================


class TestGetUnreadCount:
    """Tests for NotificationService.get_unread_count."""

    @pytest.mark.asyncio
    async def test_get_unread_count_with_unread(self, notification_service, mock_db):
        """Should return the count of unread notifications."""
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_db.execute.return_value = mock_result

        count = await notification_service.get_unread_count(user_id)

        assert count == 3

    @pytest.mark.asyncio
    async def test_get_unread_count_zero(self, notification_service, mock_db):
        """Should return 0 when all notifications are read."""
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        count = await notification_service.get_unread_count(user_id)

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_unread_count_none_returns_zero(self, notification_service, mock_db):
        """Should return 0 when the scalar result is None (no rows)."""
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result

        count = await notification_service.get_unread_count(user_id)

        assert count == 0


# ============================================================
# Error Hierarchy Tests
# ============================================================


class TestErrorHierarchy:
    """Tests for error class hierarchy and properties."""

    def test_notification_service_error_base(self):
        """NotificationServiceError should have message and status_code."""
        err = NotificationServiceError("test error", status_code=500)
        assert err.message == "test error"
        assert err.status_code == 500
        assert str(err) == "test error"

    def test_notification_not_found_error(self):
        """NotificationNotFoundError should have 404 status."""
        nid = uuid.uuid4()
        err = NotificationNotFoundError(nid)
        assert err.status_code == 404
        assert str(nid) in err.message
