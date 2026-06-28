"""Unit tests for verification decision logic service.

Tests cover:
- determine_verification_status: threshold-based decision logic (Req 5.4, 5.5)
- process_verification_decision: end-to-end verification flow
- manual_verify: Org Admin manual review decisions (Req 5.6)
- mark_processing_failed: handling corrupt/unsupported files (Req 5.7)
- Notification sending for manual review and failures
"""

import sys
import uuid
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, ".")

import pytest

from app.models.enums import VerificationStatus
from app.services.verification_service import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DocumentNotFoundError,
    InvalidVerificationStateError,
    NotificationPlaceholder,
    SubmissionNotFoundError,
    VerificationService,
    VerificationServiceError,
    determine_verification_status,
)


# ============================================================
# Tests for determine_verification_status
# ============================================================


class TestDetermineVerificationStatus:
    """Tests for the core threshold-based decision function."""

    def test_confidence_above_threshold_returns_auto_verified(self):
        """Req 5.4: confidence >= threshold → AUTO_VERIFIED."""
        result = determine_verification_status(0.85, 0.75)
        assert result == VerificationStatus.AUTO_VERIFIED

    def test_confidence_equal_to_threshold_returns_auto_verified(self):
        """Req 5.4: confidence == threshold → AUTO_VERIFIED (boundary)."""
        result = determine_verification_status(0.75, 0.75)
        assert result == VerificationStatus.AUTO_VERIFIED

    def test_confidence_below_threshold_returns_manual_review(self):
        """Req 5.5: confidence < threshold → MANUAL_REVIEW."""
        result = determine_verification_status(0.60, 0.75)
        assert result == VerificationStatus.MANUAL_REVIEW

    def test_confidence_just_below_threshold_returns_manual_review(self):
        """Req 5.5: confidence just below threshold → MANUAL_REVIEW."""
        result = determine_verification_status(0.7499, 0.75)
        assert result == VerificationStatus.MANUAL_REVIEW

    def test_confidence_zero_returns_manual_review(self):
        """Zero confidence always flags manual review."""
        result = determine_verification_status(0.0, 0.75)
        assert result == VerificationStatus.MANUAL_REVIEW

    def test_confidence_one_returns_auto_verified(self):
        """Perfect confidence always auto-verifies."""
        result = determine_verification_status(1.0, 0.75)
        assert result == VerificationStatus.AUTO_VERIFIED

    def test_default_threshold_is_0_75(self):
        """Default threshold should be 0.75."""
        assert DEFAULT_CONFIDENCE_THRESHOLD == 0.75
        # Just below default
        result = determine_verification_status(0.74)
        assert result == VerificationStatus.MANUAL_REVIEW
        # At default
        result = determine_verification_status(0.75)
        assert result == VerificationStatus.AUTO_VERIFIED

    def test_custom_threshold_high(self):
        """Custom high threshold (e.g. 0.95) requires very high confidence."""
        result = determine_verification_status(0.90, 0.95)
        assert result == VerificationStatus.MANUAL_REVIEW
        result = determine_verification_status(0.95, 0.95)
        assert result == VerificationStatus.AUTO_VERIFIED

    def test_custom_threshold_low(self):
        """Custom low threshold (e.g. 0.3) is lenient."""
        result = determine_verification_status(0.30, 0.30)
        assert result == VerificationStatus.AUTO_VERIFIED
        result = determine_verification_status(0.29, 0.30)
        assert result == VerificationStatus.MANUAL_REVIEW

    def test_clamps_confidence_above_1(self):
        """Values above 1.0 are clamped to 1.0."""
        result = determine_verification_status(1.5, 0.75)
        assert result == VerificationStatus.AUTO_VERIFIED

    def test_clamps_confidence_below_0(self):
        """Values below 0.0 are clamped to 0.0."""
        result = determine_verification_status(-0.5, 0.75)
        assert result == VerificationStatus.MANUAL_REVIEW

    def test_clamps_threshold_above_1(self):
        """Threshold above 1.0 is clamped to 1.0."""
        # confidence 1.0 >= threshold clamped to 1.0
        result = determine_verification_status(1.0, 1.5)
        assert result == VerificationStatus.AUTO_VERIFIED

    def test_clamps_threshold_below_0(self):
        """Threshold below 0.0 is clamped to 0.0."""
        # Any confidence >= 0.0 threshold
        result = determine_verification_status(0.0, -0.5)
        assert result == VerificationStatus.AUTO_VERIFIED


# ============================================================
# Tests for NotificationPlaceholder
# ============================================================


class TestNotificationPlaceholder:
    """Tests for the notification placeholder."""

    @pytest.mark.asyncio
    async def test_notify_org_admin_manual_review(self):
        """Notification is recorded for manual review."""
        notifier = NotificationPlaceholder()
        admin_id = uuid.uuid4()
        doc_id = uuid.uuid4()

        await notifier.notify_org_admin_manual_review(admin_id, doc_id, 0.65)

        assert len(notifier.sent_notifications) == 1
        notification = notifier.sent_notifications[0]
        assert notification["recipient_id"] == admin_id
        assert notification["payload"]["document_id"] == str(doc_id)
        assert notification["payload"]["confidence_score"] == 0.65

    @pytest.mark.asyncio
    async def test_notify_recipient_processing_failed(self):
        """Notification is recorded for processing failure."""
        notifier = NotificationPlaceholder()
        recipient_id = uuid.uuid4()
        doc_id = uuid.uuid4()

        await notifier.notify_recipient_processing_failed(
            recipient_id, doc_id, "File corrupted"
        )

        assert len(notifier.sent_notifications) == 1
        notification = notifier.sent_notifications[0]
        assert notification["recipient_id"] == recipient_id
        assert notification["payload"]["reason"] == "File corrupted"
        assert "re-upload" in notification["payload"]["message"]


# ============================================================
# Tests for VerificationService
# ============================================================


class FakeSubmission:
    """Fake ComplianceSubmission for testing."""

    def __init__(self, status=VerificationStatus.PENDING):
        self.id = uuid.uuid4()
        self.status = status
        self.verified_at: Optional[datetime] = None
        self.verified_by: Optional[uuid.UUID] = None


class FakeDocument:
    """Fake UploadedDocument for testing."""

    def __init__(self, submission_id: uuid.UUID):
        self.id = uuid.uuid4()
        self.submission_id = submission_id


def make_fake_db(document=None, submission=None):
    """Create a mock AsyncSession with configurable query results."""
    db = AsyncMock()

    async def fake_execute(query):
        result = MagicMock()
        # Inspect the query to determine what's being fetched
        query_str = str(query)
        if "uploaded_documents" in query_str:
            result.scalar_one_or_none.return_value = document
        elif "compliance_submissions" in query_str:
            result.scalar_one_or_none.return_value = submission
        else:
            result.scalar_one_or_none.return_value = None
        return result

    db.execute = fake_execute
    db.flush = AsyncMock()
    return db


class TestVerificationServiceProcessDecision:
    """Tests for process_verification_decision."""

    @pytest.mark.asyncio
    async def test_auto_verify_high_confidence(self):
        """Req 5.4: High confidence auto-verifies the document."""
        submission = FakeSubmission(status=VerificationStatus.PROCESSING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)
        notifier = NotificationPlaceholder()

        service = VerificationService(db=db, notification_service=notifier)
        ocr_result = {"confidence_score": 0.90}
        program_id = uuid.uuid4()

        status = await service.process_verification_decision(
            document_id=document.id,
            ocr_result=ocr_result,
            program_id=program_id,
        )

        assert status == VerificationStatus.AUTO_VERIFIED
        assert submission.status == VerificationStatus.AUTO_VERIFIED
        assert submission.verified_at is not None
        assert len(notifier.sent_notifications) == 0

    @pytest.mark.asyncio
    async def test_manual_review_low_confidence_with_notification(self):
        """Req 5.5: Low confidence flags for manual review and notifies admin."""
        submission = FakeSubmission(status=VerificationStatus.PROCESSING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)
        notifier = NotificationPlaceholder()

        service = VerificationService(db=db, notification_service=notifier)
        ocr_result = {"confidence_score": 0.50}
        program_id = uuid.uuid4()
        admin_id = uuid.uuid4()

        status = await service.process_verification_decision(
            document_id=document.id,
            ocr_result=ocr_result,
            program_id=program_id,
            org_admin_id=admin_id,
        )

        assert status == VerificationStatus.MANUAL_REVIEW
        assert submission.status == VerificationStatus.MANUAL_REVIEW
        assert submission.verified_at is None
        assert len(notifier.sent_notifications) == 1
        assert notifier.sent_notifications[0]["recipient_id"] == admin_id

    @pytest.mark.asyncio
    async def test_manual_review_no_notification_without_admin_id(self):
        """Manual review without admin_id doesn't send notification."""
        submission = FakeSubmission(status=VerificationStatus.PROCESSING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)
        notifier = NotificationPlaceholder()

        service = VerificationService(db=db, notification_service=notifier)
        ocr_result = {"confidence_score": 0.50}
        program_id = uuid.uuid4()

        status = await service.process_verification_decision(
            document_id=document.id,
            ocr_result=ocr_result,
            program_id=program_id,
            org_admin_id=None,
        )

        assert status == VerificationStatus.MANUAL_REVIEW
        assert len(notifier.sent_notifications) == 0

    @pytest.mark.asyncio
    async def test_document_not_found_raises_error(self):
        """Raises DocumentNotFoundError if document doesn't exist."""
        db = make_fake_db(document=None, submission=None)
        service = VerificationService(db=db)

        with pytest.raises(DocumentNotFoundError):
            await service.process_verification_decision(
                document_id=uuid.uuid4(),
                ocr_result={"confidence_score": 0.9},
                program_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_exact_threshold_auto_verifies(self):
        """Confidence exactly at threshold auto-verifies."""
        submission = FakeSubmission(status=VerificationStatus.PROCESSING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)

        service = VerificationService(db=db)
        ocr_result = {"confidence_score": 0.75}  # exactly at default threshold

        status = await service.process_verification_decision(
            document_id=document.id,
            ocr_result=ocr_result,
            program_id=uuid.uuid4(),
        )

        assert status == VerificationStatus.AUTO_VERIFIED


class TestVerificationServiceManualVerify:
    """Tests for manual_verify (Req 5.6)."""

    @pytest.mark.asyncio
    async def test_approve_document(self):
        """Req 5.6: Admin approves → status becomes VERIFIED."""
        submission = FakeSubmission(status=VerificationStatus.MANUAL_REVIEW)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)
        admin_id = uuid.uuid4()

        service = VerificationService(db=db)

        status = await service.manual_verify(
            document_id=document.id,
            admin_id=admin_id,
            approved=True,
            notes="Looks correct after manual inspection.",
        )

        assert status == VerificationStatus.VERIFIED
        assert submission.status == VerificationStatus.VERIFIED
        assert submission.verified_at is not None
        assert submission.verified_by == admin_id

    @pytest.mark.asyncio
    async def test_reject_document(self):
        """Req 5.6: Admin rejects → status becomes REJECTED."""
        submission = FakeSubmission(status=VerificationStatus.MANUAL_REVIEW)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)
        admin_id = uuid.uuid4()

        service = VerificationService(db=db)

        status = await service.manual_verify(
            document_id=document.id,
            admin_id=admin_id,
            approved=False,
            notes="Document appears forged.",
        )

        assert status == VerificationStatus.REJECTED
        assert submission.status == VerificationStatus.REJECTED
        assert submission.verified_at is not None
        assert submission.verified_by == admin_id

    @pytest.mark.asyncio
    async def test_cannot_verify_non_manual_review_document(self):
        """Cannot manually verify a document not in MANUAL_REVIEW state."""
        submission = FakeSubmission(status=VerificationStatus.AUTO_VERIFIED)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)

        service = VerificationService(db=db)

        with pytest.raises(InvalidVerificationStateError):
            await service.manual_verify(
                document_id=document.id,
                admin_id=uuid.uuid4(),
                approved=True,
            )

    @pytest.mark.asyncio
    async def test_cannot_verify_pending_document(self):
        """Cannot manually verify a document still in PENDING state."""
        submission = FakeSubmission(status=VerificationStatus.PENDING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)

        service = VerificationService(db=db)

        with pytest.raises(InvalidVerificationStateError):
            await service.manual_verify(
                document_id=document.id,
                admin_id=uuid.uuid4(),
                approved=True,
            )

    @pytest.mark.asyncio
    async def test_document_not_found(self):
        """Raises DocumentNotFoundError for nonexistent document."""
        db = make_fake_db(document=None, submission=None)
        service = VerificationService(db=db)

        with pytest.raises(DocumentNotFoundError):
            await service.manual_verify(
                document_id=uuid.uuid4(),
                admin_id=uuid.uuid4(),
                approved=True,
            )


class TestVerificationServiceMarkFailed:
    """Tests for mark_processing_failed (Req 5.7)."""

    @pytest.mark.asyncio
    async def test_marks_submission_as_processing_failed(self):
        """Req 5.7: Sets status to PROCESSING_FAILED."""
        submission = FakeSubmission(status=VerificationStatus.PROCESSING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)

        service = VerificationService(db=db)

        status = await service.mark_processing_failed(
            document_id=document.id,
            reason="File corrupted: unable to decode image",
        )

        assert status == VerificationStatus.PROCESSING_FAILED
        assert submission.status == VerificationStatus.PROCESSING_FAILED

    @pytest.mark.asyncio
    async def test_notifies_recipient_on_failure(self):
        """Req 5.7: Notifies recipient to re-upload."""
        submission = FakeSubmission(status=VerificationStatus.PROCESSING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)
        notifier = NotificationPlaceholder()
        recipient_id = uuid.uuid4()

        service = VerificationService(db=db, notification_service=notifier)

        await service.mark_processing_failed(
            document_id=document.id,
            reason="Unsupported format: HEIC not supported",
            recipient_id=recipient_id,
        )

        assert len(notifier.sent_notifications) == 1
        notification = notifier.sent_notifications[0]
        assert notification["recipient_id"] == recipient_id
        assert "Unsupported format" in notification["payload"]["reason"]

    @pytest.mark.asyncio
    async def test_no_notification_without_recipient_id(self):
        """No notification sent if recipient_id is not provided."""
        submission = FakeSubmission(status=VerificationStatus.PROCESSING)
        document = FakeDocument(submission_id=submission.id)
        db = make_fake_db(document=document, submission=submission)
        notifier = NotificationPlaceholder()

        service = VerificationService(db=db, notification_service=notifier)

        await service.mark_processing_failed(
            document_id=document.id,
            reason="Corrupted file",
            recipient_id=None,
        )

        assert len(notifier.sent_notifications) == 0

    @pytest.mark.asyncio
    async def test_document_not_found(self):
        """Raises DocumentNotFoundError for nonexistent document."""
        db = make_fake_db(document=None, submission=None)
        service = VerificationService(db=db)

        with pytest.raises(DocumentNotFoundError):
            await service.mark_processing_failed(
                document_id=uuid.uuid4(),
                reason="File corrupted",
            )


class TestGetProgramThreshold:
    """Tests for get_program_threshold."""

    @pytest.mark.asyncio
    async def test_returns_default_threshold(self):
        """Default threshold is 0.75."""
        db = AsyncMock()
        service = VerificationService(db=db)

        threshold = await service.get_program_threshold(uuid.uuid4())
        assert threshold == 0.75
