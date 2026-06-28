"""Property-based tests for condition evaluation consistency (P5).

**Validates: Requirements 6.6, 6.7, 6.8, 6.9, 6.10**

Property P5: Condition Evaluation Consistency - evaluate_condition is deterministic;
numeric operators satisfy mathematical relationships; None returns False except
for not_exists.
"""

import sys

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

sys.path.insert(0, ".")

from app.services.compliance_engine import evaluate_condition, VALID_OPERATORS


# ============================================================
# Strategies
# ============================================================

# Numeric strings that can be parsed as floats
numeric_strings = st.floats(
    min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False
).map(lambda x: str(x))

# Non-empty, non-whitespace strings for general testing
non_empty_strings = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=1,
    max_size=50,
)

# Operators that do numeric comparison
numeric_operators = st.sampled_from(["lte", "gte", "lt", "gt"])

# All valid operators except exists/not_exists (which don't use condition_value the same way)
comparison_operators = st.sampled_from(["lte", "gte", "eq", "neq", "lt", "gt", "contains"])

# All valid operators
all_operators = st.sampled_from(sorted(VALID_OPERATORS))

# Operators that are NOT not_exists (for None handling property)
operators_except_not_exists = st.sampled_from(
    sorted(VALID_OPERATORS - {"not_exists"})
)


# ============================================================
# Property 1: DETERMINISM - Same inputs always produce same result
# ============================================================


@given(
    operator=all_operators,
    actual_value=st.one_of(st.none(), st.text(min_size=0, max_size=50)),
    condition_value=st.text(min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_determinism(operator: str, actual_value, condition_value: str):
    """evaluate_condition is deterministic: same operator + actual_value + condition_value
    always produces the same result.

    **Validates: Requirements 6.6**
    """
    result1 = evaluate_condition(operator, actual_value, condition_value)
    result2 = evaluate_condition(operator, actual_value, condition_value)
    assert result1 == result2, (
        f"Non-deterministic result for evaluate_condition({operator!r}, {actual_value!r}, {condition_value!r}): "
        f"first call returned {result1}, second call returned {result2}"
    )


# ============================================================
# Property 2: NUMERIC RELATIONSHIPS - Mathematical consistency
# ============================================================


@given(a=numeric_strings, b=numeric_strings)
@settings(max_examples=200)
def test_lte_and_gt_are_complementary(a: str, b: str):
    """For valid numeric inputs, if lte(a, b) then not gt(a, b).
    These are mathematical complements for the same numeric pair.

    **Validates: Requirements 6.6, 6.7**
    """
    lte_result = evaluate_condition("lte", a, b)
    gt_result = evaluate_condition("gt", a, b)
    # lte(a, b) means a <= b, gt(a, b) means a > b. These are complements.
    assert lte_result != gt_result, (
        f"lte({a}, {b})={lte_result} and gt({a}, {b})={gt_result} should be complementary"
    )


@given(a=numeric_strings, b=numeric_strings)
@settings(max_examples=200)
def test_gte_and_lt_are_complementary(a: str, b: str):
    """For valid numeric inputs, if gte(a, b) then not lt(a, b).
    These are mathematical complements for the same numeric pair.

    **Validates: Requirements 6.6, 6.7**
    """
    gte_result = evaluate_condition("gte", a, b)
    lt_result = evaluate_condition("lt", a, b)
    # gte(a, b) means a >= b, lt(a, b) means a < b. These are complements.
    assert gte_result != lt_result, (
        f"gte({a}, {b})={gte_result} and lt({a}, {b})={lt_result} should be complementary"
    )


@given(a=numeric_strings, b=numeric_strings)
@settings(max_examples=200)
def test_lte_equals_lt_or_numeric_equality(a: str, b: str):
    """For valid numeric inputs, lte(a, b) == (lt(a, b) OR a == b numerically).

    **Validates: Requirements 6.6, 6.7**
    """
    lte_result = evaluate_condition("lte", a, b)
    lt_result = evaluate_condition("lt", a, b)
    a_num = float(a)
    b_num = float(b)
    numerically_equal = a_num == b_num

    assert lte_result == (lt_result or numerically_equal), (
        f"lte({a}, {b})={lte_result} should equal (lt={lt_result} or eq={numerically_equal})"
    )


# ============================================================
# Property 3: NONE HANDLING - None actual_value returns False except for not_exists
# ============================================================


@given(
    operator=operators_except_not_exists,
    condition_value=st.text(min_size=0, max_size=50),
)
@settings(max_examples=200)
def test_none_returns_false_except_not_exists(operator: str, condition_value: str):
    """For all operators except not_exists, None actual_value returns False.

    **Validates: Requirements 6.7, 6.8, 6.9**
    """
    result = evaluate_condition(operator, None, condition_value)

    if operator == "exists":
        # exists(None) should also be False
        assert result is False, (
            f"exists(None, {condition_value!r}) should be False, got {result}"
        )
    else:
        assert result is False, (
            f"evaluate_condition({operator!r}, None, {condition_value!r}) should be False, got {result}"
        )


# ============================================================
# Property 4: NOT_EXISTS IS INVERSE OF EXISTS
# ============================================================


@given(actual_value=st.one_of(st.none(), st.text(min_size=0, max_size=50)))
@settings(max_examples=200)
def test_exists_and_not_exists_are_complementary(actual_value):
    """For any value, exists(v) XOR not_exists(v) - they are logical complements.

    **Validates: Requirements 6.8, 6.9**
    """
    exists_result = evaluate_condition("exists", actual_value, "")
    not_exists_result = evaluate_condition("not_exists", actual_value, "")

    assert exists_result != not_exists_result, (
        f"exists({actual_value!r})={exists_result} and not_exists({actual_value!r})={not_exists_result} "
        f"should be complementary (XOR)"
    )


# ============================================================
# Property 5: EQ/NEQ COMPLEMENTARY
# ============================================================


@given(
    a=non_empty_strings,
    b=non_empty_strings,
)
@settings(max_examples=200)
def test_eq_and_neq_are_complementary(a: str, b: str):
    """For any non-None inputs, eq(a, b) XOR neq(a, b) - they are logical complements.

    **Validates: Requirements 6.6, 6.10**
    """
    eq_result = evaluate_condition("eq", a, b)
    neq_result = evaluate_condition("neq", a, b)

    assert eq_result != neq_result, (
        f"eq({a!r}, {b!r})={eq_result} and neq({a!r}, {b!r})={neq_result} "
        f"should be complementary (XOR)"
    )


# ============================================================
# Property 6: CASE INSENSITIVITY - eq is case-insensitive
# ============================================================


@given(text=st.from_regex(r"[a-zA-Z0-9 ]{1,50}", fullmatch=True))
@settings(max_examples=200)
def test_eq_case_insensitive_symmetry(text: str):
    """eq("ABC", "abc") == eq("abc", "ABC") - case-insensitive comparison is symmetric.

    Uses ASCII alphanumeric characters where lower/upper roundtrip is well-defined.

    **Validates: Requirements 6.10**
    """
    upper = text.upper()
    lower = text.lower()

    # eq(upper, lower) should be True since they differ only by case
    result_upper_lower = evaluate_condition("eq", upper, lower)
    result_lower_upper = evaluate_condition("eq", lower, upper)

    assert result_upper_lower == result_lower_upper, (
        f"eq({upper!r}, {lower!r})={result_upper_lower} should equal "
        f"eq({lower!r}, {upper!r})={result_lower_upper}"
    )

    # Both should be True since they are the same string ignoring case
    assert result_upper_lower is True, (
        f"eq({upper!r}, {lower!r}) should be True for case-insensitive comparison"
    )


@given(
    a=st.text(min_size=1, max_size=50),
    b=st.text(min_size=1, max_size=50),
)
@settings(max_examples=200)
def test_eq_symmetry(a: str, b: str):
    """eq(a, b) == eq(b, a) - equality comparison is symmetric regardless of case.

    **Validates: Requirements 6.10**
    """
    result_ab = evaluate_condition("eq", a, b)
    result_ba = evaluate_condition("eq", b, a)

    assert result_ab == result_ba, (
        f"eq({a!r}, {b!r})={result_ab} should equal eq({b!r}, {a!r})={result_ba} "
        f"(equality should be symmetric)"
    )
