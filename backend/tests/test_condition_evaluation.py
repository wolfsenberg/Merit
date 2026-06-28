"""Unit tests for compliance engine condition evaluation function.

Tests cover all operators: lte, gte, eq, neq, lt, gt, contains, exists, not_exists
with focus on:
- Numeric comparisons with parse-error fail-safe (Req 6.7)
- Case-insensitive string comparisons for eq and contains (Req 6.10)
- exists/not_exists checks for None and empty/whitespace values (Req 6.8, 6.9)
"""

import sys

import pytest

sys.path.insert(0, ".")

from app.services.compliance_engine import evaluate_condition


# ============================================================
# Numeric Comparison Tests (lte, gte, lt, gt)
# ============================================================


class TestNumericLte:
    """Tests for less-than-or-equal operator."""

    def test_lte_equal_values(self):
        """Equal values should satisfy lte."""
        assert evaluate_condition("lte", "3.5", "3.5") is True

    def test_lte_smaller_actual(self):
        """Smaller actual value should satisfy lte."""
        assert evaluate_condition("lte", "2.0", "3.5") is True

    def test_lte_larger_actual(self):
        """Larger actual value should not satisfy lte."""
        assert evaluate_condition("lte", "4.0", "3.5") is False

    def test_lte_integer_values(self):
        """Integer string values should work for lte."""
        assert evaluate_condition("lte", "5", "10") is True

    def test_lte_negative_values(self):
        """Negative values should work correctly."""
        assert evaluate_condition("lte", "-5", "-3") is True
        assert evaluate_condition("lte", "-1", "-3") is False


class TestNumericGte:
    """Tests for greater-than-or-equal operator."""

    def test_gte_equal_values(self):
        """Equal values should satisfy gte."""
        assert evaluate_condition("gte", "3.5", "3.5") is True

    def test_gte_larger_actual(self):
        """Larger actual value should satisfy gte."""
        assert evaluate_condition("gte", "4.0", "3.5") is True

    def test_gte_smaller_actual(self):
        """Smaller actual value should not satisfy gte."""
        assert evaluate_condition("gte", "2.0", "3.5") is False


class TestNumericLt:
    """Tests for less-than operator."""

    def test_lt_smaller_actual(self):
        """Smaller actual value should satisfy lt."""
        assert evaluate_condition("lt", "2.0", "3.5") is True

    def test_lt_equal_values(self):
        """Equal values should not satisfy lt."""
        assert evaluate_condition("lt", "3.5", "3.5") is False

    def test_lt_larger_actual(self):
        """Larger actual value should not satisfy lt."""
        assert evaluate_condition("lt", "4.0", "3.5") is False


class TestNumericGt:
    """Tests for greater-than operator."""

    def test_gt_larger_actual(self):
        """Larger actual value should satisfy gt."""
        assert evaluate_condition("gt", "4.0", "3.5") is True

    def test_gt_equal_values(self):
        """Equal values should not satisfy gt."""
        assert evaluate_condition("gt", "3.5", "3.5") is False

    def test_gt_smaller_actual(self):
        """Smaller actual value should not satisfy gt."""
        assert evaluate_condition("gt", "2.0", "3.5") is False


# ============================================================
# Numeric Parse Error Fail-Safe (Req 6.7)
# ============================================================


class TestNumericParseErrorFailSafe:
    """Tests for parse-error fail-safe behavior on numeric operators."""

    def test_non_numeric_actual_returns_false(self):
        """Non-numeric actual value should return False for numeric ops."""
        assert evaluate_condition("lte", "abc", "3.5") is False
        assert evaluate_condition("gte", "abc", "3.5") is False
        assert evaluate_condition("lt", "hello", "3.5") is False
        assert evaluate_condition("gt", "world", "3.5") is False

    def test_non_numeric_condition_returns_false(self):
        """Non-numeric condition value should return False for numeric ops."""
        assert evaluate_condition("lte", "3.5", "abc") is False
        assert evaluate_condition("gte", "3.5", "xyz") is False
        assert evaluate_condition("lt", "3.5", "not_a_number") is False
        assert evaluate_condition("gt", "3.5", "foo") is False

    def test_empty_string_actual_returns_false(self):
        """Empty string actual value should return False for numeric ops."""
        assert evaluate_condition("lte", "", "3.5") is False
        assert evaluate_condition("gte", "", "3.5") is False

    def test_whitespace_actual_returns_false(self):
        """Whitespace-only actual value should return False for numeric ops."""
        assert evaluate_condition("lte", "   ", "3.5") is False

    def test_none_actual_returns_false_for_numeric(self):
        """None actual value should return False for numeric operators."""
        assert evaluate_condition("lte", None, "3.5") is False
        assert evaluate_condition("gte", None, "3.5") is False
        assert evaluate_condition("lt", None, "3.5") is False
        assert evaluate_condition("gt", None, "3.5") is False


# ============================================================
# String Equality Tests - Case Insensitive (Req 6.10)
# ============================================================


class TestStringEq:
    """Tests for case-insensitive string equality operator."""

    def test_eq_same_case(self):
        """Same case strings should be equal."""
        assert evaluate_condition("eq", "enrolled", "enrolled") is True

    def test_eq_different_case(self):
        """Different case strings should be equal (case-insensitive)."""
        assert evaluate_condition("eq", "Enrolled", "enrolled") is True
        assert evaluate_condition("eq", "ENROLLED", "enrolled") is True
        assert evaluate_condition("eq", "enrolled", "ENROLLED") is True

    def test_eq_not_equal(self):
        """Different strings should not be equal."""
        assert evaluate_condition("eq", "dropped", "enrolled") is False

    def test_eq_with_whitespace_trimming(self):
        """Whitespace should be trimmed before comparison."""
        assert evaluate_condition("eq", "  enrolled  ", "enrolled") is True
        assert evaluate_condition("eq", "enrolled", "  enrolled  ") is True

    def test_eq_none_actual_returns_false(self):
        """None actual value should return False for eq."""
        assert evaluate_condition("eq", None, "enrolled") is False


# ============================================================
# String Inequality Tests
# ============================================================


class TestStringNeq:
    """Tests for case-insensitive string inequality operator."""

    def test_neq_different_strings(self):
        """Different strings should satisfy neq."""
        assert evaluate_condition("neq", "dropped", "enrolled") is True

    def test_neq_same_string(self):
        """Same string should not satisfy neq."""
        assert evaluate_condition("neq", "enrolled", "enrolled") is False

    def test_neq_case_insensitive(self):
        """Case-insensitive equal strings should not satisfy neq."""
        assert evaluate_condition("neq", "ENROLLED", "enrolled") is False
        assert evaluate_condition("neq", "Enrolled", "enrolled") is False

    def test_neq_none_actual_returns_false(self):
        """None actual value should return False for neq."""
        assert evaluate_condition("neq", None, "enrolled") is False


# ============================================================
# Contains Tests - Case Insensitive (Req 6.10)
# ============================================================


class TestContains:
    """Tests for case-insensitive substring contains operator."""

    def test_contains_substring_present(self):
        """Should return True when condition_value is a substring of actual."""
        assert evaluate_condition("contains", "University of Manila", "Manila") is True

    def test_contains_case_insensitive(self):
        """Should work case-insensitively."""
        assert evaluate_condition("contains", "University of Manila", "manila") is True
        assert evaluate_condition("contains", "university of manila", "MANILA") is True

    def test_contains_not_present(self):
        """Should return False when substring is not found."""
        assert evaluate_condition("contains", "University of Manila", "Cebu") is False

    def test_contains_exact_match(self):
        """Exact full match should also return True."""
        assert evaluate_condition("contains", "Manila", "Manila") is True

    def test_contains_empty_condition(self):
        """Empty condition_value should match anything (empty is substring of all)."""
        assert evaluate_condition("contains", "some text", "") is True

    def test_contains_none_actual_returns_false(self):
        """None actual value should return False for contains."""
        assert evaluate_condition("contains", None, "test") is False

    def test_contains_with_whitespace_trimming(self):
        """Whitespace should be trimmed before comparison."""
        assert evaluate_condition("contains", "  University of Manila  ", "Manila") is True


# ============================================================
# Exists Tests (Req 6.8)
# ============================================================


class TestExists:
    """Tests for exists operator - True only if value is not None and not empty/whitespace."""

    def test_exists_with_value(self):
        """Non-empty value should return True."""
        assert evaluate_condition("exists", "some value", "") is True

    def test_exists_with_number(self):
        """Numeric string should return True."""
        assert evaluate_condition("exists", "3.5", "") is True

    def test_exists_none_returns_false(self):
        """None should return False."""
        assert evaluate_condition("exists", None, "") is False

    def test_exists_empty_string_returns_false(self):
        """Empty string should return False."""
        assert evaluate_condition("exists", "", "") is False

    def test_exists_whitespace_only_returns_false(self):
        """Whitespace-only string should return False."""
        assert evaluate_condition("exists", "   ", "") is False
        assert evaluate_condition("exists", "\t", "") is False
        assert evaluate_condition("exists", "\n", "") is False
        assert evaluate_condition("exists", "  \t\n  ", "") is False


# ============================================================
# Not Exists Tests (Req 6.9)
# ============================================================


class TestNotExists:
    """Tests for not_exists operator - True only if value IS None or empty/whitespace."""

    def test_not_exists_none_returns_true(self):
        """None should return True."""
        assert evaluate_condition("not_exists", None, "") is True

    def test_not_exists_empty_returns_true(self):
        """Empty string should return True."""
        assert evaluate_condition("not_exists", "", "") is True

    def test_not_exists_whitespace_returns_true(self):
        """Whitespace-only string should return True."""
        assert evaluate_condition("not_exists", "   ", "") is True
        assert evaluate_condition("not_exists", "\t\n", "") is True

    def test_not_exists_with_value_returns_false(self):
        """Non-empty value should return False."""
        assert evaluate_condition("not_exists", "some value", "") is False

    def test_not_exists_with_number_returns_false(self):
        """Numeric string should return False."""
        assert evaluate_condition("not_exists", "3.5", "") is False


# ============================================================
# Invalid Operator Tests
# ============================================================


class TestInvalidOperator:
    """Tests for invalid operator handling."""

    def test_invalid_operator_raises_value_error(self):
        """Invalid operator should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid operator"):
            evaluate_condition("invalid", "5", "3")

    def test_empty_operator_raises_value_error(self):
        """Empty operator string should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid operator"):
            evaluate_condition("", "5", "3")
