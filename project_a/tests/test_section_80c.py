
from decimal import Decimal
import pytest

from project_a.tax_engine.section_80c import (
    calculate_80c_deduction
)


def test_80c_below_limit():
    result = calculate_80c_deduction(
        "old", Decimal("100000")
    )
    assert result == Decimal("100000")


def test_80c_at_limit():
    result = calculate_80c_deduction(
        "old", Decimal("150000")
    )
    assert result == Decimal("150000")


def test_80c_above_limit():
    result = calculate_80c_deduction(
        "old", Decimal("200000")
    )
    assert result == Decimal("150000")


def test_80c_new_regime():
    result = calculate_80c_deduction(
        "new", Decimal("150000")
    )
    assert result == Decimal("0")


def test_80c_zero_investment():
    result = calculate_80c_deduction(
        "old", Decimal("0")
    )
    assert result == Decimal("0")


def test_80c_negative_investment():
    with pytest.raises(ValueError):
        calculate_80c_deduction(
            "old", Decimal("-1000")
        )


def test_80c_invalid_regime():
    with pytest.raises(ValueError):
        calculate_80c_deduction(
            "invalid", Decimal("100000")
        )
