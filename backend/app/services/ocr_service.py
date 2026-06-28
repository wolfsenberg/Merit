"""OCR processing pipeline for document verification.

This module implements the OCR processing pipeline that extracts text from documents,
identifies structured fields based on document type, and calculates confidence scores.
The OCR engine is abstracted behind a protocol to allow mocking in tests.

Requirements: 5.2, 5.3, 5.10
"""

import re
import time
from typing import Optional, Protocol

from app.models.enums import DocumentType


# ============================================================
# OCR Engine Protocol (mockable abstraction)
# ============================================================


class OCREngine(Protocol):
    """Protocol for OCR engine implementations.

    This abstraction allows swapping between EasyOCR, PaddleOCR,
    or a mock implementation for testing.
    """

    def extract_text(self, file_content: bytes, file_type: str) -> tuple[str, float]:
        """Extract text from file content.

        Args:
            file_content: Raw bytes of the document file.
            file_type: MIME type of the file (e.g., 'application/pdf', 'image/png').

        Returns:
            A tuple of (extracted_text, engine_confidence) where engine_confidence
            is a float in [0.0, 1.0] representing the OCR engine's confidence.
        """
        ...


# ============================================================
# EasyOCR Implementation
# ============================================================


class EasyOCREngine:
    """OCR engine implementation using EasyOCR.

    This is the production implementation. It requires GPU/CPU resources
    and the easyocr package to be installed.
    """

    def __init__(self, languages: Optional[list[str]] = None):
        """Initialize EasyOCR reader.

        Args:
            languages: List of language codes for OCR. Defaults to ['en'].
        """
        self._languages = languages or ["en"]
        self._reader = None

    def _get_reader(self):
        """Lazy-load the EasyOCR reader to avoid import-time GPU allocation."""
        if self._reader is None:
            import easyocr

            self._reader = easyocr.Reader(self._languages, gpu=False)
        return self._reader

    def extract_text(self, file_content: bytes, file_type: str) -> tuple[str, float]:
        """Extract text from file content using EasyOCR.

        Args:
            file_content: Raw bytes of the document file.
            file_type: MIME type of the file.

        Returns:
            Tuple of (extracted_text, average_confidence).
        """
        reader = self._get_reader()

        # EasyOCR accepts image bytes directly for image types
        # For PDFs, we'd need to convert pages to images first
        if file_type == "application/pdf":
            # For PDF, extract text directly if possible, or convert pages to images
            # In production, use pdf2image or similar library
            # For now, treat as image bytes (EasyOCR handles many formats)
            pass

        results = reader.readtext(file_content)

        if not results:
            return "", 0.0

        # results is a list of (bbox, text, confidence)
        texts = []
        confidences = []
        for _bbox, text, confidence in results:
            texts.append(text)
            confidences.append(confidence)

        extracted_text = "\n".join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return extracted_text, avg_confidence


# ============================================================
# Expected Fields Per Document Type
# ============================================================

# Maps each document type to the list of fields we expect to extract
EXPECTED_FIELDS: dict[DocumentType, list[str]] = {
    DocumentType.GRADE_SLIP: ["gwa", "student_id", "semester"],
    DocumentType.ENROLLMENT_FORM: ["student_id", "program_name", "enrollment_status"],
    DocumentType.CERTIFICATE: ["recipient_name", "certificate_title", "date_issued"],
    DocumentType.TRANSCRIPT: ["student_id", "gwa", "program_name", "academic_year"],
    DocumentType.ID_DOCUMENT: ["full_name", "id_number", "date_of_birth"],
    DocumentType.REPORT: ["title", "author", "date"],
    DocumentType.CUSTOM: [],
}


def get_expected_fields(document_type: DocumentType) -> list[str]:
    """Get the list of expected fields for a given document type.

    Args:
        document_type: The type of document being processed.

    Returns:
        List of field names expected for this document type.
    """
    return EXPECTED_FIELDS.get(document_type, [])


# ============================================================
# Structured Data Extraction (Pattern Matching)
# ============================================================

# Regex patterns for extracting specific field values from OCR text.
# Each pattern maps a field name to a compiled regex with a named group 'value'.
FIELD_PATTERNS: dict[str, list[re.Pattern]] = {
    "gwa": [
        re.compile(r"(?:gwa|general\s*weighted\s*average|g\.?w\.?a\.?)\s*[:\-]?\s*(?P<value>\d+\.?\d*)", re.IGNORECASE),
        re.compile(r"(?:average|grade)\s*[:\-]?\s*(?P<value>\d+\.\d+)", re.IGNORECASE),
    ],
    "student_id": [
        re.compile(r"(?:student\s*(?:id|no|number|#))\s*[:\-]?\s*(?P<value>[\w\-]+)", re.IGNORECASE),
        re.compile(r"(?:id\s*(?:no|number|#))\s*[:\-]?\s*(?P<value>\d[\w\-]+)", re.IGNORECASE),
    ],
    "semester": [
        re.compile(r"(?:semester|sem)\s*[:\-]?\s*(?P<value>(?:1st|2nd|first|second|summer|midyear)[\w\s]*)", re.IGNORECASE),
        re.compile(r"(?P<value>(?:first|second|1st|2nd)\s+semester)", re.IGNORECASE),
    ],
    "program_name": [
        re.compile(r"(?:program|course|degree)\s*[:\-]?\s*(?P<value>[A-Za-z\s]+(?:Science|Engineering|Arts|Education|Business|Computing|Technology)[\w\s]*)", re.IGNORECASE),
        re.compile(r"(?:program|course|degree)\s*[:\-]?\s*(?P<value>[A-Z][A-Za-z\s]{3,})", re.IGNORECASE),
    ],
    "enrollment_status": [
        re.compile(r"(?:enrollment\s*status|status)\s*[:\-]?\s*(?P<value>enrolled|active|inactive|regular|irregular|LOA|withdrawn|graduated)", re.IGNORECASE),
        re.compile(r"(?P<value>(?:currently\s+)?enrolled|regular|irregular)", re.IGNORECASE),
    ],
    "recipient_name": [
        re.compile(r"(?:awarded?\s+to|presented?\s+to|name|recipient)\s*[:\-]?\s*(?P<value>[A-Z][a-zA-Z\s\.]+)", re.IGNORECASE),
    ],
    "certificate_title": [
        re.compile(r"(?:certificate\s+of|this\s+certifies)\s*[:\-]?\s*(?P<value>[A-Za-z\s]+)", re.IGNORECASE),
        re.compile(r"(?P<value>certificate\s+of\s+[A-Za-z\s]+)", re.IGNORECASE),
    ],
    "date_issued": [
        re.compile(r"(?:date\s*issued|issued\s*(?:on|date)?|date)\s*[:\-]?\s*(?P<value>\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})", re.IGNORECASE),
        re.compile(r"(?:date\s*issued|issued\s*(?:on|date)?|date)\s*[:\-]?\s*(?P<value>[A-Za-z]+\s+\d{1,2},?\s*\d{4})", re.IGNORECASE),
    ],
    "full_name": [
        re.compile(r"(?:full\s*name|name)\s*[:\-]?\s*(?P<value>[A-Z][a-zA-Z\s\.]+)", re.IGNORECASE),
    ],
    "id_number": [
        re.compile(r"(?:id\s*(?:no|number|#)|no\.?)\s*[:\-]?\s*(?P<value>[\w\-]+)", re.IGNORECASE),
    ],
    "date_of_birth": [
        re.compile(r"(?:date\s*of\s*birth|dob|birth\s*date|birthday)\s*[:\-]?\s*(?P<value>\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})", re.IGNORECASE),
        re.compile(r"(?:date\s*of\s*birth|dob|birth\s*date|birthday)\s*[:\-]?\s*(?P<value>[A-Za-z]+\s+\d{1,2},?\s*\d{4})", re.IGNORECASE),
    ],
    "academic_year": [
        re.compile(r"(?:academic\s*year|a\.?y\.?|school\s*year)\s*[:\-]?\s*(?P<value>\d{4}\s*[\-/]\s*\d{4})", re.IGNORECASE),
        re.compile(r"(?P<value>\d{4}\s*[\-]\s*\d{4})\s*(?:academic|school)", re.IGNORECASE),
    ],
    "title": [
        re.compile(r"(?:title|subject|report\s*title)\s*[:\-]?\s*(?P<value>[A-Za-z\s]+)", re.IGNORECASE),
    ],
    "author": [
        re.compile(r"(?:author|prepared\s*by|submitted\s*by|by)\s*[:\-]?\s*(?P<value>[A-Z][a-zA-Z\s\.]+)", re.IGNORECASE),
    ],
    "date": [
        re.compile(r"(?:date)\s*[:\-]?\s*(?P<value>\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})", re.IGNORECASE),
        re.compile(r"(?:date)\s*[:\-]?\s*(?P<value>[A-Za-z]+\s+\d{1,2},?\s*\d{4})", re.IGNORECASE),
    ],
}


def extract_structured_data(
    raw_text: str,
    document_type: DocumentType,
    expected_fields: Optional[list[str]] = None,
) -> dict[str, str]:
    """Extract structured data from raw OCR text using pattern matching.

    For each expected field of the document type, attempts to find a matching
    value using regex patterns. This is deterministic: same input always produces
    same output (Requirement 5.10).

    Args:
        raw_text: The raw text extracted by the OCR engine.
        document_type: The type of document being processed.
        expected_fields: Optional override for expected fields. If None, uses
            the default fields for the document type.

    Returns:
        Dictionary mapping field names to extracted values.
        Only fields that were successfully matched are included.
    """
    if expected_fields is None:
        expected_fields = get_expected_fields(document_type)

    extracted: dict[str, str] = {}

    for field_name in expected_fields:
        patterns = FIELD_PATTERNS.get(field_name, [])
        for pattern in patterns:
            match = pattern.search(raw_text)
            if match:
                value = match.group("value").strip()
                if value:
                    extracted[field_name] = value
                    break

    return extracted


# ============================================================
# Confidence Scoring
# ============================================================


def calculate_confidence(
    extracted_fields: dict[str, str],
    expected_fields: list[str],
    ocr_confidence: float,
) -> float:
    """Calculate confidence score for OCR extraction results.

    The confidence score is a weighted combination of:
    - Field completeness (60%): fraction of expected fields that were found
    - OCR engine confidence (40%): the OCR engine's self-reported confidence

    This ensures same inputs always produce same outputs (Requirement 5.10).

    Args:
        extracted_fields: Dictionary of successfully extracted field values.
        expected_fields: List of field names expected for this document type.
        ocr_confidence: The OCR engine's confidence score in [0.0, 1.0].

    Returns:
        Confidence score in [0.0, 1.0].

    Preconditions:
        - extracted_fields is a non-null dictionary
        - expected_fields is a list (may be empty for CUSTOM type)
        - ocr_confidence is in [0.0, 1.0]

    Postconditions:
        - Result is in [0.0, 1.0]
        - Result is deterministic for same inputs
    """
    # Clamp ocr_confidence to valid range
    ocr_confidence = max(0.0, min(1.0, ocr_confidence))

    # If no expected fields (e.g., CUSTOM type), rely entirely on OCR confidence
    if not expected_fields:
        return ocr_confidence

    # Calculate field completeness: what fraction of expected fields were found
    fields_found = sum(1 for field in expected_fields if field in extracted_fields)
    field_completeness = fields_found / len(expected_fields)

    # Weighted combination: 60% field completeness, 40% OCR confidence
    confidence = 0.6 * field_completeness + 0.4 * ocr_confidence

    # Ensure result is clamped to [0.0, 1.0]
    return max(0.0, min(1.0, confidence))


# ============================================================
# Main Processing Pipeline
# ============================================================


class OCRService:
    """Orchestrates the OCR processing pipeline.

    This service ties together text extraction, structured data extraction,
    and confidence scoring into a single pipeline.
    """

    def __init__(self, ocr_engine: Optional[OCREngine] = None):
        """Initialize OCR service with an engine implementation.

        Args:
            ocr_engine: An OCR engine implementation. If None, uses EasyOCREngine.
        """
        self._engine = ocr_engine or EasyOCREngine()

    def extract_text(self, file_content: bytes, file_type: str) -> tuple[str, float]:
        """Extract text from document content.

        Args:
            file_content: Raw bytes of the document.
            file_type: MIME type of the document.

        Returns:
            Tuple of (extracted_text, ocr_confidence).
        """
        return self._engine.extract_text(file_content, file_type)

    def process_document(
        self,
        file_content: bytes,
        file_type: str,
        document_type: DocumentType,
    ) -> dict:
        """Run the full OCR processing pipeline on a document.

        This is the main entry point for document processing. It:
        1. Extracts raw text using the OCR engine
        2. Identifies structured fields via pattern matching
        3. Calculates a confidence score

        The result is deterministic: same inputs always produce same output
        (Requirement 5.10).

        Args:
            file_content: Raw bytes of the document.
            file_type: MIME type (e.g., 'application/pdf', 'image/png').
            document_type: The document type enum for field expectations.

        Returns:
            Dictionary with keys:
                - extracted_text: The raw OCR text
                - structured_data: Dict of identified fields and values
                - confidence_score: Float in [0.0, 1.0]
                - processing_time_ms: Integer, time taken in milliseconds
                - extraction_metadata: Dict with engine details
        """
        start_time = time.perf_counter()

        # Step 1: Extract text using OCR engine
        raw_text, ocr_confidence = self.extract_text(file_content, file_type)

        # Step 2: Extract structured data via pattern matching
        expected_fields = get_expected_fields(document_type)
        structured_data = extract_structured_data(raw_text, document_type, expected_fields)

        # Step 3: Calculate confidence score
        confidence_score = calculate_confidence(structured_data, expected_fields, ocr_confidence)

        # Calculate processing time
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "extracted_text": raw_text,
            "structured_data": structured_data,
            "confidence_score": confidence_score,
            "processing_time_ms": elapsed_ms,
            "extraction_metadata": {
                "ocr_engine_confidence": ocr_confidence,
                "fields_expected": expected_fields,
                "fields_found": list(structured_data.keys()),
                "field_completeness": len(structured_data) / len(expected_fields) if expected_fields else 1.0,
            },
        }
