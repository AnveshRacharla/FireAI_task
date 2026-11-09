from decimal import Decimal
import pytest

from project_a.tax_engine.section_24b import calculate_24b_deduction


def test_higher_limit():
    result = calculate_24b_deduction(
        "old", Decimal("180000"), True
    )
    assert result == Decimal("180000")


def test_higher_limit_capped():
    result = calculate_24b_deduction(
        "old", Decimal("250000"), True
    )
    assert result == Decimal("200000")


def test_lower_limit():
    result = calculate_24b_deduction(
        "old", Decimal("25000"), False
    )
    assert result == Decimal("25000")


def test_lower_limit_capped():
    result = calculate_24b_deduction(
        "old", Decimal("50000"), False
    )
    assert result == Decimal("30000")


def test_new_regime():
    result = calculate_24b_deduction(
        "new", Decimal("200000"), True
    )
    assert result == Decimal("0")


def test_zero_interest():
    result = calculate_24b_deduction(
        "old", Decimal("0"), True
    )
    assert result == Decimal("0")


def test_negative_interest():
    with pytest.raises(ValueError):
        calculate_24b_deduction(
            "old", Decimal("-1000"), True
        )


def test_invalid_regime():
    with pytest.raises(ValueError):
        calculate_24b_deduction(
            "invalid", Decimal("100000"), True
        )
        