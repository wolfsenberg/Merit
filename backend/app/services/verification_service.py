"""Verification decision logic for document processing.

This module implements the verification decision service that determines
whether a document is auto-verified, flagged for manual review, or marked
as failed based on OCR confidence scores and program thresholds.

Requirements: 5.4, 5.5, 5.6, 5.7
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_submission import ComplianceSubmission
from app.models.enums import NotificationType, VerificationStatus
from app.models.uploaded_document import UploadedDocument

# Default confidence threshold for auto-verification (configurable per program)
DEFAULT_CONFIDENCE_THRESHOLD = 0.75


class VerificationServiceError(Exception):
    """Base exception for verification service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentNotFoundError(VerificationServiceError):
    """Raised when a document is not found."""

    def __init__(self, document_id: uuid.UUID):
        super().__init__(f"Document {document_id} not found", status_code=404)


class SubmissionNotFoundError(VerificationServiceError):
    """Raised when a compliance submission is not found."""

    def __init__(self, submission_id: uuid.UUID):
        super().__init__(f"Submission {submission_id} not found", status_code=404)


class InvalidVerificationStateError(VerificationServiceError):
    """Raised when a verification action is not allowed in the current state."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


# ============================================================
# Notification Placeholder
# ============================================================


class NotificationPlaceholder:
    """Placeholder notification service for sending alerts.

    In production, this would integrate with the full NotificationService.
    For now, it records notifications for later delivery.
    """

    def __init__(self):
        self.sent_notifications: list[dict] = []

    async def notify_org_admin_manual_review(
        self,
        admin_id: uuid.UUID,
        document_id: uuid.UUID,
        confidence_score: float,
    ) -> None:
        """Notify Org Admin that a document requires manual review.

        Args:
            admin_id: The organization admin's user ID.
            document_id: The document that needs review.
            confidence_score: The confidence score that triggered manual review.
        """
        self.sent_notifications.append({
            "recipient_id": admin_id,
            "notification_type": NotificationType.MANUAL_REVIEW_REQUIRED,
            "payload": {
                "document_id": str(document_id),
                "confidence_score": confidence_score,
                "message": "A document requires manual review due to low confidence score.",
            },
        })

    async def notify_recipient_processing_failed(
        self,
        recipient_id: uuid.UUID,
        document_id: uuid.UUID,
        reason: str,
    ) -> None:
        """Notify Recipient that document processing failed.

        Args:
            recipient_id: The recipient's user ID.
            document_id: The document that failed processing.
            reason: The reason for the failure.
        """
        self.sent_notifications.append({
            "recipient_id": recipient_id,
            "notification_type": NotificationType.DOCUMENT_VERIFIED,
            "payload": {
                "document_id": str(document_id),
                "status": "processing_failed",
                "reason": reason,
                "message": "Document processing failed. Please re-upload your document.",
            },
        })


# ============================================================
# Core Verification Decision Functions
# ============================================================


def determine_verification_status(
    confidence_score: float, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> VerificationStatus:
    """Determine the verification status based on confidence score vs threshold.

    This is the core decision logic:
    - If confidence >= threshold → AUTO_VERIFIED
    - If confidence < threshold → MANUAL_REVIEW

    Args:
        confidence_score: The OCR confidence score in [0.0, 1.0].
        threshold: The program's confidence threshold (default 0.75).

    Returns:
        VerificationStatus.AUTO_VERIFIED or VerificationStatus.MANUAL_REVIEW

    Preconditions:
        - confidence_score is in [0.0, 1.0]
        - threshold is in [0.0, 1.0]

    Postconditions:
        - Returns AUTO_VERIFIED if and only if confidence_score >= threshold
        - Returns MANUAL_REVIEW if and only if confidence_score < threshold
    """
    # Clamp inputs to valid range
    confidence_score = max(0.0, min(1.0, confidence_score))
    threshold = max(0.0, min(1.0, threshold))

    if confidence_score >= threshold:
        return VerificationStatus.AUTO_VERIFIED
    else:
        return VerificationStatus.MANUAL_REVIEW


# ============================================================
# Verification Service
# ============================================================


class VerificationService:
    """Service handling verification decisions for OCR-processed documents.

    Orchestrates the decision logic after OCR processing:
    - Auto-verify high-confidence results
    - Flag low-confidence results for manual review
    - Handle processing failures
    - Process manual verification decisions by Org Admins
    """

    def __init__(
        self,
        db: AsyncSession,
        notification_service: Optional[NotificationPlaceholder] = None,
    ):
        """Initialize the verification service.

        Args:
            db: Async database session.
            notification_service: Optional notification service for sending alerts.
        """
        self.db = db
        self.notifications = notification_service or NotificationPlaceholder()

    async def get_program_threshold(self, program_id: uuid.UUID) -> float:
        """Get the confidence threshold for a program.

        Currently returns the default threshold. In production, this would
        look up a per-program configurable threshold.

        Args:
            program_id: The program's ID.

        Returns:
            The confidence threshold for the program (default 0.75).
        """
        # TODO: Look up per-program threshold from a program_settings table
        # For now, return the default
        return DEFAULT_CONFIDENCE_THRESHOLD

    async def process_verification_decision(
        self,
        document_id: uuid.UUID,
        ocr_result: dict,
        program_id: uuid.UUID,
        org_admin_id: Optional[uuid.UUID] = None,
    ) -> VerificationStatus:
        """Process the verification decision after OCR completes.

        This is the main entry point after OCR processing. It:
        1. Retrieves the program's confidence threshold
        2. Determines the verification status based on confidence
        3. Updates the document/submission status
        4. Sends notifications if manual review is needed

        Args:
            document_id: The ID of the processed document.
            ocr_result: Dictionary with OCR results including 'confidence_score'.
            program_id: The program ID (used to look up threshold).
            org_admin_id: Optional org admin ID for notifications.

        Returns:
            The determined VerificationStatus.

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
        """
        confidence_score = ocr_result.get("confidence_score", 0.0)

        # Get program-specific threshold
        threshold = await self.get_program_threshold(program_id)

        # Determine verification status
        status = determine_verification_status(confidence_score, threshold)

        # Update the document's submission status
        document = await self._get_document(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        # Update submission status
        submission = await self._get_submission(document.submission_id)
        if submission is not None:
            submission.status = status
            if status == VerificationStatus.AUTO_VERIFIED:
                submission.verified_at = datetime.now(timezone.utc)

        # Send notifications for manual review
        if status == VerificationStatus.MANUAL_REVIEW and org_admin_id is not None:
            await self.notifications.notify_org_admin_manual_review(
                admin_id=org_admin_id,
                document_id=document_id,
                confidence_score=confidence_score,
            )

        await self.db.flush()
        return status

    async def manual_verify(
        self,
        document_id: uuid.UUID,
        admin_id: uuid.UUID,
        approved: bool,
        notes: Optional[str] = None,
    ) -> VerificationStatus:
        """Process a manual verification decision by an Org Admin.

        An Org Admin reviews a flagged document and decides to verify or reject it.

        Args:
            document_id: The document being reviewed.
            admin_id: The Org Admin making the decision.
            approved: True to verify, False to reject.
            notes: Optional notes from the admin about the decision.

        Returns:
            The new VerificationStatus (VERIFIED or REJECTED).

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
            InvalidVerificationStateError: If the document is not in MANUAL_REVIEW state.
        """
        document = await self._get_document(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        submission = await self._get_submission(document.submission_id)
        if submission is None:
            raise SubmissionNotFoundError(document.submission_id)

        # Only allow manual verification on documents in MANUAL_REVIEW status
        if submission.status != VerificationStatus.MANUAL_REVIEW:
            raise InvalidVerificationStateError(
                f"Document {document_id} is not in MANUAL_REVIEW status "
                f"(current status: {submission.status.value}). "
                f"Only documents flagged for manual review can be manually verified."
            )

        # Apply the decision
        new_status = VerificationStatus.VERIFIED if approved else VerificationStatus.REJECTED
        submission.status = new_status
        submission.verified_at = datetime.now(timezone.utc)
        submission.verified_by = admin_id

        await self.db.flush()
        return new_status

    async def mark_processing_failed(
        self,
        document_id: uuid.UUID,
        reason: str,
        recipient_id: Optional[uuid.UUID] = None,
    ) -> VerificationStatus:
        """Mark a document as failed processing and notify the recipient.

        This is called when OCR processing fails due to file corruption,
        unsupported format, or other unrecoverable errors.

        Args:
            document_id: The document that failed processing.
            reason: Description of why processing failed.
            recipient_id: Optional recipient ID for notification.

        Returns:
            VerificationStatus.PROCESSING_FAILED

        Raises:
            DocumentNotFoundError: If the document doesn't exist.
        """
        document = await self._get_document(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        submission = await self._get_submission(document.submission_id)
        if submission is not None:
            submission.status = VerificationStatus.PROCESSING_FAILED

        # Notify recipient to re-upload
        if recipient_id is not None:
            await self.notifications.notify_recipient_processing_failed(
                recipient_id=recipient_id,
                document_id=document_id,
                reason=reason,
            )

        await self.db.flush()
        return VerificationStatus.PROCESSING_FAILED

    # ============================================================
    # Private Helpers
    # ============================================================

    async def _get_document(self, document_id: uuid.UUID) -> Optional[UploadedDocument]:
        """Retrieve a document by ID.

        Args:
            document_id: The document's primary key.

        Returns:
            The UploadedDocument or None if not found.
        """
        result = await self.db.execute(
            select(UploadedDocument).where(UploadedDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def _get_submission(
        self, submission_id: uuid.UUID
    ) -> Optional[ComplianceSubmission]:
        """Retrieve a compliance submission by ID.

        Args:
            submission_id: The submission's primary key.

        Returns:
            The ComplianceSubmission or None if not found.
        """
        result = await self.db.execute(
            select(ComplianceSubmission).where(ComplianceSubmission.id == submission_id)
        )
        return result.scalar_one_or_none()
