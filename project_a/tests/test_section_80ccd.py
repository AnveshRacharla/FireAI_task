from decimal import Decimal
import pytest

from project_a.tax_engine.section_80ccd import (
    calculate_80ccd_1b_deduction
)


def test_below_limit():
    result = calculate_80ccd_1b_deduction(
        "old", Decimal("30000")
    )
    assert result == Decimal("30000")


def test_at_limit():
    result = calculate_80ccd_1b_deduction(
        "old", Decimal("50000")
    )
    assert result == Decimal("50000")


def test_above_limit():
    result = calculate_80ccd_1b_deduction(
        "old", Decimal("80000")
    )
    assert result == Decimal("50000")


def test_new_regime():
    result = calculate_80ccd_1b_deduction(
        "new", Decimal("50000")
    )
    assert result == Decimal("0")


def test_zero_contribution():
    result = calculate_80ccd_1b_deduction(
        "old", Decimal("0")
    )
    assert result == Decimal("0")


def test_negative_contribution():
    with pytest.raises(ValueError):
        calculate_80ccd_1b_deduction(
            "old", Decimal("-1000")
        )


def test_invalid_regime():
    with pytest.raises(ValueError):
        calculate_80ccd_1b_deduction(
            "invalid", Decimal("50000")
        )