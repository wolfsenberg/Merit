"""Enum definitions for Merit Platform models."""

import enum


class UserRole(str, enum.Enum):
    """User role types."""

    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    RECIPIENT = "recipient"


class ProgramStatus(str, enum.Enum):
    """Program lifecycle statuses."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class RequirementType(str, enum.Enum):
    """Types of program requirements."""

    ACADEMIC_GWA = "academic_gwa"
    ENROLLMENT_STATUS = "enrollment_status"
    DOCUMENT_SUBMISSION = "document_submission"
    MILESTONE_COMPLETION = "milestone_completion"
    ATTENDANCE = "attendance"
    CUSTOM = "custom"


class ApplicationStatus(str, enum.Enum):
    """Application lifecycle statuses."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class VerificationStatus(str, enum.Enum):
    """Document verification statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    AUTO_VERIFIED = "auto_verified"
    MANUAL_REVIEW = "manual_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    PROCESSING_FAILED = "processing_failed"


class DocumentType(str, enum.Enum):
    """Uploaded document types."""

    GRADE_SLIP = "grade_slip"
    ENROLLMENT_FORM = "enrollment_form"
    CERTIFICATE = "certificate"
    TRANSCRIPT = "transcript"
    ID_DOCUMENT = "id_document"
    REPORT = "report"
    CUSTOM = "custom"


class EligibilityStatus(str, enum.Enum):
    """Eligibility evaluation statuses."""

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    PENDING_VERIFICATION = "pending_verification"
    PARTIAL = "partial"


class NotificationType(str, enum.Enum):
    """Notification event types."""

    APPLICATION_RECEIVED = "application_received"
    DOCUMENT_VERIFIED = "document_verified"
    ELIGIBILITY_DETERMINED = "eligibility_determined"
    FUNDS_RELEASED = "funds_released"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    PROGRAM_UPDATE = "program_update"
