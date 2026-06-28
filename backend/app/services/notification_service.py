"""Notification service.

Manages in-app notifications for system events including document verification,
eligibility determination, fund disbursement, and manual review requests.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)


# =============================================================================
# Error Classes
# =============================================================================


class NotificationServiceError(Exception):
    """Base exception for notification service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotificationNotFoundError(NotificationServiceError):
    """Raised when a notification is not found."""

    def __init__(self, notification_id: uuid.UUID):
        super().__init__(
            f"Notification {notification_id} not found",
            status_code=404,
        )


# =============================================================================
# Notification Title Templates
# =============================================================================

_NOTIFICATION_TITLES = {
    NotificationType.DOCUMENT_VERIFIED: "Document Verified",
    NotificationType.ELIGIBILITY_DETERMINED: "Eligibility Determined",
    NotificationType.FUNDS_RELEASED: "Funds Released",
    NotificationType.MANUAL_REVIEW_REQUIRED: "Manual Review Required",
    NotificationType.APPLICATION_RECEIVED: "Application Received",
    NotificationType.PROGRAM_UPDATE: "Program Update",
}

_NOTIFICATION_MESSAGES = {
    NotificationType.DOCUMENT_VERIFIED: "Your document has been verified successfully.",
    NotificationType.ELIGIBILITY_DETERMINED: "Your eligibility status has been determined.",
    NotificationType.FUNDS_RELEASED: "Funds have been released to your wallet.",
    NotificationType.MANUAL_REVIEW_REQUIRED: "A document requires your manual review.",
    NotificationType.APPLICATION_RECEIVED: "A new application has been received.",
    NotificationType.PROGRAM_UPDATE: "A program you are enrolled in has been updated.",
}


# =============================================================================
# NotificationService
# =============================================================================


class NotificationService:
    """Service for managing user notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_notification(
        self,
        user_id: uuid.UUID,
        notification_type: NotificationType,
        payload: Optional[dict] = None,
        title: Optional[str] = None,
        message: Optional[str] = None,
    ) -> NotificationResponse:
        """Send a notification to a user.

        Args:
            user_id: The target user's ID.
            notification_type: The type of notification event.
            payload: Optional JSON payload with event-specific data.
            title: Optional custom title (uses default template if not provided).
            message: Optional custom message (uses default template if not provided).

        Returns:
            The created notification response.
        """
        resolved_title = title or _NOTIFICATION_TITLES.get(
            notification_type, "Notification"
        )
        resolved_message = message or _NOTIFICATION_MESSAGES.get(notification_type)

        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=notification_type,
            title=resolved_title,
            message=resolved_message,
            payload=payload,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(notification)
        await self.db.flush()

        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            payload=notification.payload,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )

    async def get_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> NotificationListResponse:
        """Get notifications for a user with optional unread filter.

        Args:
            user_id: The user whose notifications to fetch.
            unread_only: If True, return only unread notifications.
            limit: Maximum number of notifications to return.
            offset: Number of notifications to skip.

        Returns:
            A list response with notifications, total count, and unread count.
        """
        # Build base query
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712

        # Get total count for the filtered query
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get unread count (always unfiltered by read status)
        unread_query = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        # Fetch notifications with pagination, ordered by most recent first
        query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return NotificationListResponse(
            notifications=[
                NotificationResponse(
                    id=n.id,
                    user_id=n.user_id,
                    notification_type=n.notification_type,
                    title=n.title,
                    message=n.message,
                    payload=n.payload,
                    is_read=n.is_read,
                    created_at=n.created_at,
                    read_at=n.read_at,
                )
                for n in notifications
            ],
            total=total,
            unread_count=unread_count,
        )

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationResponse:
        """Mark a notification as read.

        Args:
            notification_id: The notification to mark as read.
            user_id: The user who owns the notification (for authorization).

        Returns:
            The updated notification response.

        Raises:
            NotificationNotFoundError: If the notification doesn't exist or doesn't belong to the user.
        """
        query = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()

        if notification is None:
            raise NotificationNotFoundError(notification_id)

        now = datetime.now(timezone.utc)
        notification.is_read = True
        notification.read_at = now

        await self.db.flush()

        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            payload=notification.payload,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get the count of unread notifications for a user.

        Args:
            user_id: The user whose unread count to fetch.

        Returns:
            The number of unread notifications.
        """
        query = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
