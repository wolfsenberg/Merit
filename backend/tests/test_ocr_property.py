"""Property-based tests for confidence scoring and verification determinism (P4).

**Validates: Requirements 5.10**

Property P4: Document Processing Determinism - Same document content always
yields identical structured_data and confidence_score. This file uses Hypothesis
to verify determinism, range constraints, threshold consistency, and monotonicity
of the confidence scoring and verification decision functions.
"""

import sys

sys.path.insert(0, ".")

import pytest
from hypothesis import given, settings, assume, note
from hypothesis import strategies as st

from app.models.enums import DocumentType, VerificationStatus
from app.services.ocr_service import (
    EXPECTED_FIELDS,
    OCRService,
    calculate_confidence,
    extract_structured_data,
    get_expected_fields,
)
from app.services.verification_service import (
    determine_verification_status,
)


# ============================================================
# Strategies
# ============================================================

# Document types that have expected fields (non-empty)
document_types_with_fields = st.sampled_from([
    dt for dt in DocumentType if EXPECTED_FIELDS.get(dt)
])

# All document types including CUSTOM
all_document_types = st.sampled_from(list(DocumentType))

# Generate arbitrary text strings for OCR simulation
raw_text_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=0,
    max_size=500,
)

# Confidence values in a broad range (may be out of [0,1] to test clamping)
broad_confidence = st.floats(min_value=-1.0, max_value=2.0, allow_nan=False, allow_infinity=False)

# Confidence values strictly in [0, 1]
valid_confidence = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Threshold values in [0, 1]
valid_threshold = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Generate field names (subset of known fields)
known_field_names = [
    "gwa", "student_id", "semester", "program_name", "enrollment_status",
    "recipient_name", "certificate_title", "date_issued", "full_name",
    "id_number", "date_of_birth", "academic_year", "title", "author", "date",
]

field_name_strategy = st.sampled_from(known_field_names)

# Generate a dictionary of extracted fields (field_name -> value)
extracted_fields_strategy = st.dictionaries(
    keys=field_name_strategy,
    values=st.text(min_size=1, max_size=50),
    min_size=0,
    max_size=8,
)

# Generate a list of expected fields
expected_fields_strategy = st.lists(
    field_name_strategy,
    min_size=0,
    max_size=8,
    unique=True,
)


# ============================================================
# Property 1: DETERMINISM - extract_structured_data is idempotent
# ============================================================


@given(
    raw_text=raw_text_strategy,
    doc_type=all_document_types,
)
@settings(max_examples=200)
def test_extract_structured_data_is_deterministic(raw_text: str, doc_type: DocumentType):
    """Same raw_text + document_type always produces identical structured_data.

    **Validates: Requirements 5.10**

    The extraction function uses deterministic regex pattern matching, so
    repeated calls with identical inputs must yield identical outputs.
    """
    result1 = extract_structured_data(raw_text, doc_type)
    result2 = extract_structured_data(raw_text, doc_type)

    assert result1 == result2, (
        f"Non-deterministic extraction for doc_type={doc_type.value}: "
        f"first={result1}, second={result2}"
    )


# ============================================================
# Property 2: DETERMINISM - calculate_confidence is deterministic
# ============================================================


@given(
    extracted_fields=extracted_fields_strategy,
    expected_fields=expected_fields_strategy,
    ocr_confidence=broad_confidence,
)
@settings(max_examples=200)
def test_calculate_confidence_is_deterministic(
    extracted_fields: dict,
    expected_fields: list,
    ocr_confidence: float,
):
    """Same extracted_fields + expected_fields + ocr_confidence always produces same score.

    **Validates: Requirements 5.10**

    calculate_confidence is a pure function with no side effects or randomness,
    so identical inputs must yield identical outputs.
    """
    score1 = calculate_confidence(extracted_fields, expected_fields, ocr_confidence)
    score2 = calculate_confidence(extracted_fields, expected_fields, ocr_confidence)

    assert score1 == score2, (
        f"Non-deterministic confidence: first={score1}, second={score2}"
    )


# ============================================================
# Property 3: CONFIDENCE RANGE - always in [0.0, 1.0]
# ============================================================


@given(
    extracted_fields=extracted_fields_strategy,
    expected_fields=expected_fields_strategy,
    ocr_confidence=broad_confidence,
)
@settings(max_examples=300)
def test_confidence_always_in_valid_range(
    extracted_fields: dict,
    expected_fields: list,
    ocr_confidence: float,
):
    """calculate_confidence always returns a value in [0.0, 1.0] for any inputs.

    **Validates: Requirements 5.10**

    Even with out-of-range ocr_confidence values (e.g., -1.0 or 2.0),
    the function must clamp the result to [0.0, 1.0].
    """
    score = calculate_confidence(extracted_fields, expected_fields, ocr_confidence)

    assert 0.0 <= score <= 1.0, (
        f"Confidence score {score} is out of range [0.0, 1.0] "
        f"with ocr_confidence={ocr_confidence}, "
        f"extracted={len(extracted_fields)} fields, expected={len(expected_fields)} fields"
    )


# ============================================================
# Property 4: THRESHOLD DECISION - deterministic and consistent
# ============================================================


@given(
    confidence_score=valid_confidence,
    threshold=valid_threshold,
)
@settings(max_examples=300)
def test_determine_verification_status_is_deterministic_and_consistent(
    confidence_score: float,
    threshold: float,
):
    """determine_verification_status is deterministic and consistent with threshold comparison.

    **Validates: Requirements 5.10**

    - Same inputs always produce same output (determinism)
    - confidence >= threshold → AUTO_VERIFIED
    - confidence < threshold → MANUAL_REVIEW
    """
    result1 = determine_verification_status(confidence_score, threshold)
    result2 = determine_verification_status(confidence_score, threshold)

    # Determinism
    assert result1 == result2, (
        f"Non-deterministic verification status: "
        f"confidence={confidence_score}, threshold={threshold}, "
        f"first={result1}, second={result2}"
    )

    # Consistency with threshold comparison
    if confidence_score >= threshold:
        assert result1 == VerificationStatus.AUTO_VERIFIED, (
            f"Expected AUTO_VERIFIED for confidence={confidence_score} >= threshold={threshold}, "
            f"got {result1}"
        )
    else:
        assert result1 == VerificationStatus.MANUAL_REVIEW, (
            f"Expected MANUAL_REVIEW for confidence={confidence_score} < threshold={threshold}, "
            f"got {result1}"
        )


# ============================================================
# Property 5: FIELD COMPLETENESS MONOTONICITY
# ============================================================


@given(
    expected_fields=st.lists(field_name_strategy, min_size=2, max_size=6, unique=True),
    ocr_confidence=valid_confidence,
)
@settings(max_examples=200)
def test_more_fields_found_yields_higher_or_equal_confidence(
    expected_fields: list,
    ocr_confidence: float,
):
    """If more expected fields are found, confidence should be >= than with fewer fields.

    **Validates: Requirements 5.10**

    The confidence formula is: 0.6 * (fields_found / expected_count) + 0.4 * ocr_confidence.
    With the same expected_fields and ocr_confidence, adding more extracted fields
    (that match expected ones) should never decrease confidence. This tests monotonicity
    of confidence with respect to field completeness.
    """
    assume(len(expected_fields) >= 2)

    # Create a subset: fewer fields found
    fewer_fields = {expected_fields[0]: "value1"}

    # Create a superset: more fields found (includes the fewer set)
    more_fields = {field: f"value_{i}" for i, field in enumerate(expected_fields)}

    score_fewer = calculate_confidence(fewer_fields, expected_fields, ocr_confidence)
    score_more = calculate_confidence(more_fields, expected_fields, ocr_confidence)

    assert score_more >= score_fewer, (
        f"Monotonicity violated: more fields ({len(more_fields)}) yielded score {score_more} "
        f"< fewer fields ({len(fewer_fields)}) yielded score {score_fewer} "
        f"with expected={expected_fields}, ocr_confidence={ocr_confidence}"
    )


# ============================================================
# Property 5b: Monotonicity at intermediate levels
# ============================================================


@given(
    expected_fields=st.lists(field_name_strategy, min_size=3, max_size=6, unique=True),
    ocr_confidence=valid_confidence,
    split_index=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=200)
def test_field_completeness_monotonicity_incremental(
    expected_fields: list,
    ocr_confidence: float,
    split_index: int,
):
    """Adding one more matching field never decreases confidence.

    **Validates: Requirements 5.10**

    For any subset A ⊂ B of expected fields, confidence(B) >= confidence(A)
    when ocr_confidence is held constant.
    """
    assume(split_index < len(expected_fields))

    # Smaller subset
    subset_a = {field: f"val_{i}" for i, field in enumerate(expected_fields[:split_index])}
    # Larger subset (superset of A)
    subset_b = {field: f"val_{i}" for i, field in enumerate(expected_fields[:split_index + 1])}

    score_a = calculate_confidence(subset_a, expected_fields, ocr_confidence)
    score_b = calculate_confidence(subset_b, expected_fields, ocr_confidence)

    assert score_b >= score_a, (
        f"Adding field did not increase confidence: "
        f"score_a={score_a} (fields={list(subset_a.keys())}), "
        f"score_b={score_b} (fields={list(subset_b.keys())})"
    )
