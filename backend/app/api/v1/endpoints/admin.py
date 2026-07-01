"""Admin API routes.

Provides endpoints for:
- GET /admin/audit-logs - Query audit logs with filtering (Super Admin only)
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogQueryParams
from app.services.audit_service import AuditService

router = APIRouter()


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="Query audit logs",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions (Super Admin required)"},
    },
)
async def get_audit_logs(
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_time: Optional[datetime] = Query(None, description="Filter logs after this time"),
    end_time: Optional[datetime] = Query(None, description="Filter logs before this time"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> AuditLogListResponse:
    """Query audit logs with filtering.

    Only accessible by Super Admin users.
    Supports filtering by user, action, resource type, and time range.
    Results are ordered by most recent first.
    """
    params = AuditLogQueryParams(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    service = AuditService(db=db)
    return await service.query_logs(params=params)
