"""Audit logging service.

Provides append-only audit logging for all state-changing operations.
No update or delete methods are exposed to enforce immutability.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit import (
    AuditLogListResponse,
    AuditLogQueryParams,
    AuditLogResponse,
)

# =============================================================================
# AuditService
# =============================================================================


class AuditService:
    """Append-only audit logging service.

    This service intentionally does NOT provide update or delete methods
    to enforce the append-only nature of audit logs (Requirement 11.5).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[uuid.UUID] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLogResponse:
        """Create a new audit log entry.

        Args:
            action: The action performed (e.g., "compliance_evaluation", "funds_disbursed").
            resource_type: The type of resource affected (e.g., "program", "transaction").
            resource_id: The ID of the affected resource.
            user_id: The ID of the user who performed the action (None for system actions).
            details: Optional JSON details about the action.
            ip_address: The IP address of the request origin.

        Returns:
            The created audit log entry response.
        """
        audit_log = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(audit_log)
        await self.db.flush()

        return AuditLogResponse(
            id=audit_log.id,
            user_id=audit_log.user_id,
            action=audit_log.action,
            resource_type=audit_log.resource_type,
            resource_id=audit_log.resource_id,
            details=audit_log.details,
            ip_address=audit_log.ip_address,
            created_at=audit_log.created_at,
        )

    async def query_logs(
        self,
        params: AuditLogQueryParams,
    ) -> AuditLogListResponse:
        """Query audit logs with filtering.

        Supports filtering by user, action, resource type, and time range.

        Args:
            params: Query parameters including filters, limit, and offset.

        Returns:
            A list response with matching audit log entries and total count.
        """
        # Build base query
        query = select(AuditLog)

        # Apply filters
        if params.user_id is not None:
            query = query.where(AuditLog.user_id == params.user_id)

        if params.action is not None:
            query = query.where(AuditLog.action == params.action)

        if params.resource_type is not None:
            query = query.where(AuditLog.resource_type == params.resource_type)

        if params.start_time is not None:
            query = query.where(AuditLog.created_at >= params.start_time)

        if params.end_time is not None:
            query = query.where(AuditLog.created_at <= params.end_time)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Fetch logs with pagination, ordered by most recent first
        query = query.order_by(AuditLog.created_at.desc()).limit(params.limit).offset(params.offset)
        result = await self.db.execute(query)
        logs = result.scalars().all()

        return AuditLogListResponse(
            logs=[
                AuditLogResponse(
                    id=log.id,
                    user_id=log.user_id,
                    action=log.action,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    details=log.details,
                    ip_address=log.ip_address,
                    created_at=log.created_at,
                )
                for log in logs
            ],
            total=total,
        )
