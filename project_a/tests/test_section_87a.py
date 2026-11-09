from decimal import Decimal
import pytest

from project_a.tax_engine.section_87a import calculate_87a_rebate


def test_old_regime_eligible():
    result = calculate_87a_rebate(
        "old", Decimal("500000"), Decimal("12500")
    )
    assert result == Decimal("12500")


def test_old_regime_above_threshold():
    result = calculate_87a_rebate(
        "old", Decimal("510000"), Decimal("15000")
    )
    assert result == Decimal("0")


def test_new_regime_eligible():
    result = calculate_87a_rebate(
        "new", Decimal("700000"), Decimal("25000")
    )
    assert result == Decimal("25000")


def test_new_regime_above_threshold():
    result = calculate_87a_rebate(
        "new", Decimal("710000"), Decimal("30000")
    )
    assert result == Decimal("0")


def test_rebate_cannot_exceed_tax():
    result = calculate_87a_rebate(
        "new", Decimal("600000"), Decimal("10000")
    )
    assert result == Decimal("10000")


def test_zero_tax():
    result = calculate_87a_rebate(
        "old", Decimal("400000"), Decimal("0")
    )
    assert result == Decimal("0")


def test_negative_income():
    with pytest.raises(ValueError):
        calculate_87a_rebate(
            "old", Decimal("-1000"), Decimal("5000")
        )


def test_invalid_regime():
    with pytest.raises(ValueError):
        calculate_87a_rebate(
            "invalid", Decimal("400000"), Decimal("5000")
        )