
from decimal import Decimal
import pytest

from project_a.tax_engine.deductions import (
    calculate_standard_deduction
)


def test_old_regime_standard_deduction():
    result = calculate_standard_deduction(
        Decimal("1200000"), "old"
    )
    assert result == Decimal("50000")


def test_new_regime_standard_deduction():
    result = calculate_standard_deduction(
        Decimal("1200000"), "new"
    )
    assert result == Decimal("75000")


def test_salary_below_deduction_limit():
    result = calculate_standard_deduction(
        Decimal("40000"), "new"
    )
    assert result == Decimal("40000")


def test_zero_salary():
    result = calculate_standard_deduction(
        Decimal("0"), "old"
    )
    assert result == Decimal("0")


def test_negative_salary():
    with pytest.raises(ValueError):
        calculate_standard_deduction(
            Decimal("-1000"), "new"
        )


def test_invalid_regime():
    with pytest.raises(ValueError):
        calculate_standard_deduction(
            Decimal("500000"), "other"
        )
