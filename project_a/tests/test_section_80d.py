from decimal import Decimal
import pytest

from project_a.tax_engine.section_80d import calculate_80d_deduction


def test_both_non_senior():
    result = calculate_80d_deduction(
        "old", Decimal("20000"), Decimal("20000"), False, False
    )
    assert result == Decimal("40000")


def test_both_senior():
    result = calculate_80d_deduction(
        "old", Decimal("60000"), Decimal("60000"), True, True
    )
    assert result == Decimal("100000")


def test_only_parents_senior():
    result = calculate_80d_deduction(
        "old", Decimal("20000"), Decimal("60000"), False, True
    )
    assert result == Decimal("70000")


def test_only_self_family_senior():
    result = calculate_80d_deduction(
        "old", Decimal("60000"), Decimal("20000"), True, False
    )
    assert result == Decimal("70000")


def test_new_regime():
    result = calculate_80d_deduction(
        "new", Decimal("50000"), Decimal("50000"), True, True
    )
    assert result == Decimal("0")


def test_zero_premiums():
    result = calculate_80d_deduction(
        "old", Decimal("0"), Decimal("0"), False, False
    )
    assert result == Decimal("0")


def test_negative_premium():
    with pytest.raises(ValueError):
        calculate_80d_deduction(
            "old", Decimal("-1000"), Decimal("20000"), False, False
        )


def test_invalid_regime():
    with pytest.raises(ValueError):
        calculate_80d_deduction(
            "invalid", Decimal("20000"), Decimal("20000"), False, False
        )
        