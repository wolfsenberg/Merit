"""Pydantic schemas for notification requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import NotificationType


class NotificationResponse(BaseModel):
    """Schema for a notification response."""

    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: NotificationType
    title: str
    message: Optional[str] = None
    payload: Optional[dict] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Schema for a paginated list of notifications."""

    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Schema for unread notification count."""

    unread_count: int
