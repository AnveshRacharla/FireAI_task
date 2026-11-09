
from decimal import Decimal
import pytest

from project_a.tax_engine.hra import calculate_hra_exemption


def test_hra_metro_city():
    result = calculate_hra_exemption(
        "old",
        Decimal("600000"),
        Decimal("0"),
        Decimal("240000"),
        Decimal("240000"),
        True
    )
    assert result == Decimal("180000.00")


def test_hra_non_metro_city():
    result = calculate_hra_exemption(
        "old",
        Decimal("600000"),
        Decimal("0"),
        Decimal("240000"),
        Decimal("240000"),
        False
    )
    assert result == Decimal("180000.00")


def test_actual_hra_is_lowest():
    result = calculate_hra_exemption(
        "old",
        Decimal("600000"),
        Decimal("0"),
        Decimal("50000"),
        Decimal("300000"),
        True
    )
    assert result == Decimal("50000")


def test_no_rent_paid():
    result = calculate_hra_exemption(
        "old",
        Decimal("600000"),
        Decimal("0"),
        Decimal("240000"),
        Decimal("0"),
        True
    )
    assert result == Decimal("0")


def test_new_regime_no_hra_exemption():
    result = calculate_hra_exemption(
        "new",
        Decimal("600000"),
        Decimal("0"),
        Decimal("240000"),
        Decimal("240000"),
        True
    )
    assert result == Decimal("0")


def test_negative_rent():
    with pytest.raises(ValueError):
        calculate_hra_exemption(
            "old",
            Decimal("600000"),
            Decimal("0"),
            Decimal("240000"),
            Decimal("-10000"),
            True
        )


def test_invalid_regime():
    with pytest.raises(ValueError):
        calculate_hra_exemption(
            "invalid",
            Decimal("600000"),
            Decimal("0"),
            Decimal("240000"),
            Decimal("240000"),
            True
        )
