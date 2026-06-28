"""Document verification API routes.

Provides endpoints for:
- POST /documents/upload - Upload a compliance document (Recipient)
- GET /documents/{id}/ocr - Get OCR result for a document (Org Admin, Recipient)
- POST /documents/{id}/verify - Manual verification decision (Org Admin)

Requirements: 5.1, 5.6
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_roles
from app.models.enums import DocumentType, UserRole, VerificationStatus
from app.models.ocr_result import OCRResult
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.schemas.document import UploadDocumentResponse
from app.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
    DocumentServiceError,
    FileTooLargeError,
    InvalidFileTypeError,
)
from app.services.verification_service import (
    DocumentNotFoundError as VerificationDocNotFoundError,
    InvalidVerificationStateError,
    VerificationService,
    VerificationServiceError,
)

router = APIRouter()


# ============================================================
# Request/Response Schemas
# ============================================================

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ManualVerifyRequest(BaseModel):
    """Request schema for manual document verification."""

    approved: bool = Field(..., description="True to verify, False to reject")
    notes: Optional[str] = Field(None, description="Optional admin notes about the decision")


class ManualVerifyResponse(BaseModel):
    """Response schema for manual verification result."""

    document_id: uuid.UUID
    status: VerificationStatus
    verified_by: uuid.UUID
    notes: Optional[str] = None


class OCRResultResponse(BaseModel):
    """Response schema for OCR results."""

    id: uuid.UUID
    document_id: uuid.UUID
    submission_id: uuid.UUID
    extracted_text: Optional[str] = None
    structured_data: Optional[dict[str, Any]] = None
    confidence_score: float
    processing_time_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Endpoints
# ============================================================


@router.post(
    "/upload",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a compliance document",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        413: {"description": "File too large (max 10MB)"},
        415: {"description": "Unsupported file type"},
        422: {"description": "Validation error"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    document_type: DocumentType = Form(..., description="Type of document being uploaded"),
    submission_id: uuid.UUID = Form(..., description="Compliance submission ID"),
    current_user: User = Depends(require_roles(UserRole.RECIPIENT)),
    db: AsyncSession = Depends(get_db),
) -> UploadDocumentResponse:
    """Upload a compliance document for verification.

    Only recipients can upload documents. The file is validated for type and size,
    encrypted at rest, and stored with a PENDING verification status.
    """
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must have a filename",
        )

    # Read file content
    file_content = await file.read()

    service = DocumentService(db=db)
    try:
        result = await service.upload_document(
            file_content=file_content,
            filename=file.filename,
            document_type=document_type,
            submission_id=submission_id,
        )
        await db.commit()
        return result
    except FileTooLargeError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=e.message)
    except InvalidFileTypeError as e:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=e.message)
    except DocumentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/{document_id}/ocr",
    response_model=OCRResultResponse,
    summary="Get OCR result for a document",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Document or OCR result not found"},
    },
)
async def get_ocr_result(
    document_id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN, UserRole.RECIPIENT)),
    db: AsyncSession = Depends(get_db),
) -> OCRResultResponse:
    """Get the OCR processing result for a document.

    Available to Org Admins and Recipients. Recipients can only view OCR results
    for their own documents.
    """
    # Verify document exists
    doc_result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    document = doc_result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    # For recipients, verify they own the document via submission
    if current_user.role == UserRole.RECIPIENT:
        from app.models.compliance_submission import ComplianceSubmission

        sub_result = await db.execute(
            select(ComplianceSubmission).where(
                ComplianceSubmission.id == document.submission_id
            )
        )
        submission = sub_result.scalar_one_or_none()
        if submission is None or submission.recipient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this document",
            )

    # Fetch OCR result for the document
    ocr_query = await db.execute(
        select(OCRResult).where(OCRResult.document_id == document_id)
    )
    ocr_result = ocr_query.scalar_one_or_none()

    if ocr_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OCR result not found for document {document_id}",
        )

    return OCRResultResponse.model_validate(ocr_result)


@router.post(
    "/{document_id}/verify",
    response_model=ManualVerifyResponse,
    summary="Manually verify or reject a document",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Document not found"},
        409: {"description": "Document is not in MANUAL_REVIEW status"},
    },
)
async def manual_verify_document(
    document_id: uuid.UUID,
    request: ManualVerifyRequest,
    current_user: User = Depends(require_roles(UserRole.ORG_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ManualVerifyResponse:
    """Manually verify or reject a document flagged for review.

    Only Org Admins can perform manual verification. The document must be
    in MANUAL_REVIEW status.
    """
    service = VerificationService(db=db)
    try:
        new_status = await service.manual_verify(
            document_id=document_id,
            admin_id=current_user.id,
            approved=request.approved,
            notes=request.notes,
        )
        await db.commit()
        return ManualVerifyResponse(
            document_id=document_id,
            status=new_status,
            verified_by=current_user.id,
            notes=request.notes,
        )
    except VerificationDocNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    except InvalidVerificationStateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except VerificationServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
