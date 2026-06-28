"""Unit tests for OCR processing pipeline service.

Tests cover:
- Structured data extraction from OCR text (pattern matching per document type)
- Confidence scoring based on field completeness and OCR engine confidence
- OCR pipeline determinism (same input → same output, Requirement 5.10)
- Expected fields per document type
- Integration of the OCR service pipeline
"""

import sys

sys.path.insert(0, ".")

import pytest

from app.models.enums import DocumentType
from app.services.ocr_service import (
    EXPECTED_FIELDS,
    OCRService,
    calculate_confidence,
    extract_structured_data,
    get_expected_fields,
)


# ============================================================
# Mock OCR Engine for Testing
# ============================================================


class MockOCREngine:
    """A mock OCR engine that returns configurable text and confidence."""

    def __init__(self, text: str = "", confidence: float = 0.9):
        self._text = text
        self._confidence = confidence

    def extract_text(self, file_content: bytes, file_type: str) -> tuple[str, float]:
        """Return the pre-configured text and confidence."""
        return self._text, self._confidence


# ============================================================
# Tests for get_expected_fields
# ============================================================


class TestGetExpectedFields:
    """Tests for get_expected_fields function."""

    def test_grade_slip_fields(self):
        """Grade slip should expect gwa, student_id, semester."""
        fields = get_expected_fields(DocumentType.GRADE_SLIP)
        assert "gwa" in fields
        assert "student_id" in fields
        assert "semester" in fields

    def test_enrollment_form_fields(self):
        """Enrollment form should expect student_id, program_name, enrollment_status."""
        fields = get_expected_fields(DocumentType.ENROLLMENT_FORM)
        assert "student_id" in fields
        assert "program_name" in fields
        assert "enrollment_status" in fields

    def test_certificate_fields(self):
        """Certificate should expect recipient_name, certificate_title, date_issued."""
        fields = get_expected_fields(DocumentType.CERTIFICATE)
        assert "recipient_name" in fields
        assert "certificate_title" in fields
        assert "date_issued" in fields

    def test_transcript_fields(self):
        """Transcript should expect student_id, gwa, program_name, academic_year."""
        fields = get_expected_fields(DocumentType.TRANSCRIPT)
        assert "student_id" in fields
        assert "gwa" in fields
        assert "program_name" in fields
        assert "academic_year" in fields

    def test_id_document_fields(self):
        """ID document should expect full_name, id_number, date_of_birth."""
        fields = get_expected_fields(DocumentType.ID_DOCUMENT)
        assert "full_name" in fields
        assert "id_number" in fields
        assert "date_of_birth" in fields

    def test_report_fields(self):
        """Report should expect title, author, date."""
        fields = get_expected_fields(DocumentType.REPORT)
        assert "title" in fields
        assert "author" in fields
        assert "date" in fields

    def test_custom_returns_empty(self):
        """Custom type should return an empty list."""
        fields = get_expected_fields(DocumentType.CUSTOM)
        assert fields == []

    def test_all_document_types_have_entries(self):
        """Every DocumentType should have an entry in EXPECTED_FIELDS."""
        for doc_type in DocumentType:
            assert doc_type in EXPECTED_FIELDS


# ============================================================
# Tests for extract_structured_data
# ============================================================


class TestExtractStructuredData:
    """Tests for structured data extraction via pattern matching."""

    def test_grade_slip_extraction(self):
        """Should extract GWA, student ID, and semester from grade slip text."""
        text = """
        University of the Philippines
        Grade Slip
        Student ID: 2023-12345
        Semester: 1st Semester 2023-2024
        GWA: 1.75
        """
        result = extract_structured_data(text, DocumentType.GRADE_SLIP)
        assert "gwa" in result
        assert "1.75" in result["gwa"]
        assert "student_id" in result
        assert "2023-12345" in result["student_id"]
        assert "semester" in result

    def test_enrollment_form_extraction(self):
        """Should extract student ID, program, and enrollment status."""
        text = """
        Enrollment Form
        Student ID: 2022-67890
        Program: Bachelor of Science in Computer Science
        Enrollment Status: Enrolled
        """
        result = extract_structured_data(text, DocumentType.ENROLLMENT_FORM)
        assert "student_id" in result
        assert "2022-67890" in result["student_id"]
        assert "enrollment_status" in result
        assert "enrolled" in result["enrollment_status"].lower()

    def test_certificate_extraction(self):
        """Should extract recipient name, title, and date from certificate."""
        text = """
        Certificate of Completion
        This certifies that
        Awarded to: Juan Dela Cruz
        Date Issued: 01/15/2024
        """
        result = extract_structured_data(text, DocumentType.CERTIFICATE)
        assert "recipient_name" in result
        assert "Juan Dela Cruz" in result["recipient_name"]
        assert "date_issued" in result

    def test_id_document_extraction(self):
        """Should extract name, ID number, and date of birth."""
        text = """
        Republic of the Philippines
        National ID
        Full Name: Maria Santos Garcia
        ID No: 1234-5678-9012
        Date of Birth: 05/20/1998
        """
        result = extract_structured_data(text, DocumentType.ID_DOCUMENT)
        assert "full_name" in result
        assert "Maria Santos Garcia" in result["full_name"]
        assert "id_number" in result
        assert "date_of_birth" in result

    def test_empty_text_returns_empty_dict(self):
        """Empty text should return empty extracted data."""
        result = extract_structured_data("", DocumentType.GRADE_SLIP)
        assert result == {}

    def test_no_matching_patterns_returns_empty(self):
        """Text with no recognizable patterns should return empty dict."""
        text = "This is just random text with no structured data at all."
        result = extract_structured_data(text, DocumentType.GRADE_SLIP)
        assert result == {}

    def test_custom_type_returns_empty(self):
        """Custom document type with no expected fields returns empty dict."""
        text = "Student ID: 2023-12345 GWA: 1.50"
        result = extract_structured_data(text, DocumentType.CUSTOM)
        assert result == {}

    def test_partial_extraction(self):
        """When only some fields are found, should return only those."""
        text = "Student ID: 2023-99999"
        result = extract_structured_data(text, DocumentType.GRADE_SLIP)
        assert "student_id" in result
        # gwa and semester not in text, so shouldn't be in result
        assert "gwa" not in result
        assert "semester" not in result

    def test_determinism_same_input_same_output(self):
        """Same input text and document type should always produce identical output (Req 5.10)."""
        text = """
        Grade Slip
        Student ID: 2023-00001
        GWA: 2.00
        Semester: 2nd Semester
        """
        result1 = extract_structured_data(text, DocumentType.GRADE_SLIP)
        result2 = extract_structured_data(text, DocumentType.GRADE_SLIP)
        result3 = extract_structured_data(text, DocumentType.GRADE_SLIP)
        assert result1 == result2 == result3

    def test_expected_fields_override(self):
        """Should respect custom expected_fields list."""
        text = "Student ID: 2023-55555 GWA: 1.25"
        # Only look for student_id
        result = extract_structured_data(
            text, DocumentType.GRADE_SLIP, expected_fields=["student_id"]
        )
        assert "student_id" in result
        # gwa is in the text but not in our expected_fields override
        assert "gwa" not in result


# ============================================================
# Tests for calculate_confidence
# ============================================================


class TestCalculateConfidence:
    """Tests for confidence scoring function."""

    def test_all_fields_found_high_ocr_confidence(self):
        """All fields found + high OCR confidence should yield high score."""
        extracted = {"gwa": "1.75", "student_id": "2023-12345", "semester": "1st"}
        expected = ["gwa", "student_id", "semester"]
        score = calculate_confidence(extracted, expected, 0.95)
        # 0.6 * 1.0 + 0.4 * 0.95 = 0.6 + 0.38 = 0.98
        assert score == pytest.approx(0.98, abs=0.01)

    def test_no_fields_found_low_ocr_confidence(self):
        """No fields found + low OCR confidence should yield low score."""
        extracted = {}
        expected = ["gwa", "student_id", "semester"]
        score = calculate_confidence(extracted, expected, 0.2)
        # 0.6 * 0.0 + 0.4 * 0.2 = 0.0 + 0.08 = 0.08
        assert score == pytest.approx(0.08, abs=0.01)

    def test_partial_fields_found(self):
        """Partial field extraction should yield intermediate score."""
        extracted = {"student_id": "2023-12345"}
        expected = ["gwa", "student_id", "semester"]
        score = calculate_confidence(extracted, expected, 0.9)
        # 0.6 * (1/3) + 0.4 * 0.9 = 0.2 + 0.36 = 0.56
        assert score == pytest.approx(0.56, abs=0.01)

    def test_no_expected_fields_uses_only_ocr_confidence(self):
        """With no expected fields (CUSTOM type), should return OCR confidence directly."""
        score = calculate_confidence({}, [], 0.85)
        assert score == pytest.approx(0.85, abs=0.01)

    def test_result_always_in_valid_range(self):
        """Confidence should always be in [0.0, 1.0] regardless of inputs."""
        # Edge case: very high OCR confidence
        score = calculate_confidence(
            {"a": "1", "b": "2", "c": "3"},
            ["a", "b", "c"],
            1.0,
        )
        assert 0.0 <= score <= 1.0

        # Edge case: zero OCR confidence
        score = calculate_confidence({}, ["a", "b"], 0.0)
        assert 0.0 <= score <= 1.0

    def test_ocr_confidence_clamped_above_one(self):
        """OCR confidence > 1.0 should be clamped to 1.0."""
        score = calculate_confidence({"a": "1"}, ["a"], 1.5)
        # 0.6 * 1.0 + 0.4 * 1.0 = 1.0
        assert score == pytest.approx(1.0, abs=0.01)

    def test_ocr_confidence_clamped_below_zero(self):
        """OCR confidence < 0.0 should be clamped to 0.0."""
        score = calculate_confidence({"a": "1"}, ["a"], -0.5)
        # 0.6 * 1.0 + 0.4 * 0.0 = 0.6
        assert score == pytest.approx(0.6, abs=0.01)

    def test_determinism_same_inputs_same_output(self):
        """Same inputs should always produce same confidence (Req 5.10)."""
        extracted = {"gwa": "1.5", "student_id": "123"}
        expected = ["gwa", "student_id", "semester"]
        ocr_conf = 0.88

        scores = [calculate_confidence(extracted, expected, ocr_conf) for _ in range(10)]
        assert all(s == scores[0] for s in scores)

    def test_field_completeness_weight(self):
        """Field completeness should have 60% weight."""
        # All fields found, OCR confidence = 0
        score = calculate_confidence(
            {"a": "1", "b": "2"},
            ["a", "b"],
            0.0,
        )
        # 0.6 * 1.0 + 0.4 * 0.0 = 0.6
        assert score == pytest.approx(0.6, abs=0.01)

    def test_ocr_confidence_weight(self):
        """OCR confidence should have 40% weight."""
        # No fields found, OCR confidence = 1.0
        score = calculate_confidence({}, ["a", "b"], 1.0)
        # 0.6 * 0.0 + 0.4 * 1.0 = 0.4
        assert score == pytest.approx(0.4, abs=0.01)

    def test_extra_fields_in_extracted_do_not_affect_score(self):
        """Extra fields beyond expected should not increase score."""
        extracted = {"gwa": "1.75", "student_id": "123", "extra_field": "value"}
        expected = ["gwa", "student_id", "semester"]
        score = calculate_confidence(extracted, expected, 0.9)
        # Only 2/3 expected fields found
        # 0.6 * (2/3) + 0.4 * 0.9 = 0.4 + 0.36 = 0.76
        assert score == pytest.approx(0.76, abs=0.01)


# ============================================================
# Tests for OCRService Pipeline Integration
# ============================================================


class TestOCRServicePipeline:
    """Integration tests for the full OCR service pipeline."""

    def test_process_document_returns_expected_keys(self):
        """Process document should return all expected result keys."""
        mock_text = "Student ID: 2023-12345\nGWA: 1.75\nSemester: 1st Semester"
        engine = MockOCREngine(text=mock_text, confidence=0.92)
        service = OCRService(ocr_engine=engine)

        result = service.process_document(
            file_content=b"fake file content",
            file_type="image/png",
            document_type=DocumentType.GRADE_SLIP,
        )

        assert "extracted_text" in result
        assert "structured_data" in result
        assert "confidence_score" in result
        assert "processing_time_ms" in result
        assert "extraction_metadata" in result

    def test_process_document_extracts_correct_fields(self):
        """Should extract the correct structured fields from the text."""
        mock_text = "Student ID: 2023-12345\nGWA: 1.75\nSemester: 2nd Semester"
        engine = MockOCREngine(text=mock_text, confidence=0.9)
        service = OCRService(ocr_engine=engine)

        result = service.process_document(
            file_content=b"content",
            file_type="image/png",
            document_type=DocumentType.GRADE_SLIP,
        )

        assert result["structured_data"]["student_id"] == "2023-12345"
        assert "1.75" in result["structured_data"]["gwa"]

    def test_process_document_confidence_score_in_range(self):
        """Confidence score should always be in [0.0, 1.0]."""
        engine = MockOCREngine(text="random text", confidence=0.5)
        service = OCRService(ocr_engine=engine)

        result = service.process_document(
            file_content=b"content",
            file_type="image/png",
            document_type=DocumentType.GRADE_SLIP,
        )

        assert 0.0 <= result["confidence_score"] <= 1.0

    def test_process_document_determinism(self):
        """Same file content and type should always produce identical results (Req 5.10)."""
        mock_text = "Student ID: 2023-00001\nGWA: 2.00\nSemester: 1st Semester"
        engine = MockOCREngine(text=mock_text, confidence=0.88)
        service = OCRService(ocr_engine=engine)

        results = [
            service.process_document(
                file_content=b"same content",
                file_type="image/png",
                document_type=DocumentType.GRADE_SLIP,
            )
            for _ in range(5)
        ]

        # All results should have identical extracted_text, structured_data, confidence_score
        for r in results[1:]:
            assert r["extracted_text"] == results[0]["extracted_text"]
            assert r["structured_data"] == results[0]["structured_data"]
            assert r["confidence_score"] == results[0]["confidence_score"]

    def test_process_document_empty_text(self):
        """Empty OCR text should result in low confidence and empty fields."""
        engine = MockOCREngine(text="", confidence=0.0)
        service = OCRService(ocr_engine=engine)

        result = service.process_document(
            file_content=b"corrupted content",
            file_type="image/png",
            document_type=DocumentType.GRADE_SLIP,
        )

        assert result["extracted_text"] == ""
        assert result["structured_data"] == {}
        assert result["confidence_score"] == 0.0

    def test_process_document_custom_type(self):
        """CUSTOM document type should have no expected fields, score = OCR confidence."""
        engine = MockOCREngine(text="some arbitrary text", confidence=0.75)
        service = OCRService(ocr_engine=engine)

        result = service.process_document(
            file_content=b"content",
            file_type="application/pdf",
            document_type=DocumentType.CUSTOM,
        )

        assert result["structured_data"] == {}
        assert result["confidence_score"] == pytest.approx(0.75, abs=0.01)

    def test_process_document_metadata_contains_field_info(self):
        """Extraction metadata should contain field completeness information."""
        mock_text = "Student ID: 2023-11111"
        engine = MockOCREngine(text=mock_text, confidence=0.85)
        service = OCRService(ocr_engine=engine)

        result = service.process_document(
            file_content=b"content",
            file_type="image/png",
            document_type=DocumentType.GRADE_SLIP,
        )

        metadata = result["extraction_metadata"]
        assert "fields_expected" in metadata
        assert "fields_found" in metadata
        assert "field_completeness" in metadata
        assert "ocr_engine_confidence" in metadata
        assert metadata["ocr_engine_confidence"] == 0.85
        # Only student_id found out of 3 expected
        assert metadata["field_completeness"] == pytest.approx(1 / 3, abs=0.01)

    def test_extract_text_delegates_to_engine(self):
        """extract_text should delegate to the underlying engine."""
        engine = MockOCREngine(text="hello world", confidence=0.99)
        service = OCRService(ocr_engine=engine)

        text, conf = service.extract_text(b"content", "image/png")

        assert text == "hello world"
        assert conf == 0.99

    def test_process_document_processing_time_recorded(self):
        """Processing time should be a non-negative integer."""
        engine = MockOCREngine(text="GWA: 1.25", confidence=0.8)
        service = OCRService(ocr_engine=engine)

        result = service.process_document(
            file_content=b"content",
            file_type="image/png",
            document_type=DocumentType.GRADE_SLIP,
        )

        assert isinstance(result["processing_time_ms"], int)
        assert result["processing_time_ms"] >= 0


# ============================================================
# Tests for Transcript Document Type
# ============================================================


class TestTranscriptExtraction:
    """Tests for transcript document type extraction."""

    def test_transcript_with_all_fields(self):
        """Should extract all transcript fields when present."""
        text = """
        Official Transcript of Records
        Student ID: 2021-54321
        Program: Bachelor of Science in Information Technology
        GWA: 1.50
        Academic Year: 2023-2024
        """
        result = extract_structured_data(text, DocumentType.TRANSCRIPT)
        assert "student_id" in result
        assert "gwa" in result
        assert "academic_year" in result

    def test_transcript_with_alternative_gwa_format(self):
        """Should handle alternative GWA labeling."""
        text = "General Weighted Average: 2.25\nStudent No: STU-2023-001"
        result = extract_structured_data(text, DocumentType.TRANSCRIPT)
        assert "gwa" in result
        assert "2.25" in result["gwa"]


# ============================================================
# Tests for Pattern Matching Edge Cases
# ============================================================


class TestPatternMatchingEdgeCases:
    """Edge case tests for pattern matching extraction."""

    def test_gwa_with_colon_separator(self):
        """GWA field with colon separator should be extracted."""
        text = "GWA: 1.00"
        result = extract_structured_data(text, DocumentType.GRADE_SLIP)
        assert result.get("gwa") == "1.00"

    def test_gwa_with_dash_separator(self):
        """GWA field with dash separator should be extracted."""
        text = "GWA - 3.50"
        result = extract_structured_data(text, DocumentType.GRADE_SLIP)
        assert "gwa" in result
        assert "3.50" in result["gwa"]

    def test_gwa_integer_value(self):
        """GWA with integer value (no decimal) should be extracted."""
        text = "GWA: 2"
        result = extract_structured_data(text, DocumentType.GRADE_SLIP)
        assert "gwa" in result
        assert "2" in result["gwa"]

    def test_enrollment_status_various_values(self):
        """Various enrollment status values should be recognized."""
        for status in ["Enrolled", "Active", "Regular", "Irregular", "LOA"]:
            text = f"Enrollment Status: {status}"
            result = extract_structured_data(text, DocumentType.ENROLLMENT_FORM)
            assert "enrollment_status" in result, f"Failed for status: {status}"

    def test_date_formats_supported(self):
        """Both numeric and text date formats should be extracted."""
        # Numeric format
        text1 = "Date Issued: 01/15/2024"
        result1 = extract_structured_data(text1, DocumentType.CERTIFICATE)
        assert "date_issued" in result1

        # Text format
        text2 = "Date Issued: January 15, 2024"
        result2 = extract_structured_data(text2, DocumentType.CERTIFICATE)
        assert "date_issued" in result2
