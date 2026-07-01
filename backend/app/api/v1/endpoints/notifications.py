"""Notification API routes.

Provides endpoints for:
- GET /notifications - Get user notifications (any authenticated user)
- PUT /notifications/{id}/read - Mark notification as read (owner only)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationService,
)

router = APIRouter()


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Get user notifications",
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_notifications(
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    """Get notifications for the current authenticated user.

    Returns a paginated list of notifications with unread count.
    Supports filtering to show only unread notifications.
    """
    service = NotificationService(db=db)
    return await service.get_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Notification not found or does not belong to user"},
    },
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """Mark a notification as read.

    Only the owner of the notification can mark it as read.
    Returns 404 if the notification doesn't exist or belongs to another user.
    """
    service = NotificationService(db=db)
    try:
        return await service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id,
        )
    except NotificationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
