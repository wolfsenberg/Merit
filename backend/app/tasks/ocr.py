"""OCR processing background tasks for Celery and ARQ.

This module defines async tasks that process documents through the OCR pipeline.
Tasks are queued via Celery (routed to the 'ocr' queue) or ARQ.
"""

import uuid

from app.core.celery_app import celery_app


@celery_app.task(
    name="app.tasks.ocr.process_document_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="ocr",
)
def process_document_task(self, document_id: str, submission_id: str) -> dict:
    """Celery task to process a document through the OCR pipeline.

    This task:
    1. Loads the document from storage
    2. Runs OCR text extraction
    3. Extracts structured data
    4. Calculates confidence score
    5. Stores OCR result in database

    Args:
        document_id: UUID string of the document to process.
        submission_id: UUID string of the compliance submission.

    Returns:
        Dictionary with processing results including confidence_score.
    """
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            _process_document_async(document_id, submission_id)
        )
        return result
    except Exception as exc:
        # Retry on transient failures
        raise self.retry(exc=exc)
    finally:
        loop.close()


async def _process_document_async(document_id: str, submission_id: str) -> dict:
    """Async implementation of document processing.

    This function is the core async processing logic that can be invoked
    by both Celery tasks and ARQ jobs.

    Args:
        document_id: UUID string of the document.
        submission_id: UUID string of the submission.

    Returns:
        Dict with OCR processing results.
    """
    from app.core.database import async_session_factory
    from app.models.enums import VerificationStatus
    from app.models.ocr_result import OCRResult
    from app.models.uploaded_document import UploadedDocument
    from app.services.document_service import (
        decrypt_file_content,
        get_or_create_encryption_key,
    )
    from app.services.ocr_service import OCRService

    async with async_session_factory() as session:
        # Step 1: Load the document record
        from sqlalchemy import select

        doc_id = uuid.UUID(document_id)
        sub_id = uuid.UUID(submission_id)

        stmt = select(UploadedDocument).where(UploadedDocument.id == doc_id)
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()

        if document is None:
            return {"error": f"Document {document_id} not found", "success": False}

        # Step 2: Load and decrypt the file
        try:
            with open(document.storage_path, "rb") as f:
                stored_data = f.read()

            nonce = stored_data[:12]
            encrypted_data = stored_data[12:]
            encryption_key = get_or_create_encryption_key()
            file_content = decrypt_file_content(encrypted_data, encryption_key, nonce)
        except Exception:
            # File corruption or missing file
            return {
                "error": "Failed to read or decrypt document file",
                "success": False,
                "status": VerificationStatus.PROCESSING_FAILED.value,
            }

        # Step 3: Run OCR pipeline
        ocr_service = OCRService()
        ocr_result_data = ocr_service.process_document(
            file_content=file_content,
            file_type=document.mime_type,
            document_type=document.document_type,
        )

        # Step 4: Store OCR result
        ocr_record = OCRResult(
            id=uuid.uuid4(),
            submission_id=sub_id,
            document_id=doc_id,
            extracted_text=ocr_result_data["extracted_text"],
            structured_data=ocr_result_data["structured_data"],
            confidence_score=ocr_result_data["confidence_score"],
            extraction_metadata=ocr_result_data["extraction_metadata"],
            processing_time_ms=ocr_result_data["processing_time_ms"],
        )

        session.add(ocr_record)
        await session.commit()

        return {
            "success": True,
            "ocr_result_id": str(ocr_record.id),
            "confidence_score": ocr_result_data["confidence_score"],
            "structured_data": ocr_result_data["structured_data"],
            "processing_time_ms": ocr_result_data["processing_time_ms"],
        }


# ============================================================
# ARQ Job Definition
# ============================================================


async def arq_process_document(ctx: dict, document_id: str, submission_id: str) -> dict:
    """ARQ async job for document OCR processing.

    This function is registered with the ARQ worker and processes
    documents asynchronously.

    Args:
        ctx: ARQ context dictionary.
        document_id: UUID string of the document.
        submission_id: UUID string of the submission.

    Returns:
        Dict with OCR processing results.
    """
    return await _process_document_async(document_id, submission_id)


# ARQ function registry for worker configuration
ARQ_FUNCTIONS = [arq_process_document]
