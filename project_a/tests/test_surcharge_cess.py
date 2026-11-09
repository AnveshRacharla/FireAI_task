from decimal import Decimal
import pytest

from project_a.tax_engine.surcharge_cess import (
    get_surcharge_details,
    calculate_surcharge_and_cess
)


def test_no_surcharge_below_50_lakh():
    rate, threshold = get_surcharge_details(
        Decimal("4000000"), "old"
    )
    assert rate == Decimal("0")
    assert threshold == Decimal("0")


def test_surcharge_above_50_lakh():
    rate, threshold = get_surcharge_details(
        Decimal("6000000"), "old"
    )
    assert rate == Decimal("0.10")
    assert threshold == Decimal("5000000")


def test_surcharge_above_1_crore():
    rate, threshold = get_surcharge_details(
        Decimal("15000000"), "old"
    )
    assert rate == Decimal("0.15")
    assert threshold == Decimal("10000000")


def test_surcharge_above_2_crore():
    rate, threshold = get_surcharge_details(
        Decimal("30000000"), "old"
    )
    assert rate == Decimal("0.25")
    assert threshold == Decimal("20000000")


def test_old_regime_above_5_crore():
    rate, threshold = get_surcharge_details(
        Decimal("60000000"), "old"
    )
    assert rate == Decimal("0.37")
    assert threshold == Decimal("50000000")


def test_new_regime_above_5_crore():
    rate, threshold = get_surcharge_details(
        Decimal("60000000"), "new"
    )
    assert rate == Decimal("0.25")
    assert threshold == Decimal("50000000")


def test_cess_is_4_percent():
    result = calculate_surcharge_and_cess(
        Decimal("4000000"),
        Decimal("500000"),
        "old"
    )
    assert result["surcharge"] == Decimal("0")
    assert result["cess"] == Decimal("20000.00")
    assert result["total_tax"] == Decimal("520000.00")


def test_marginal_relief():
    result = calculate_surcharge_and_cess(
        taxable_income=Decimal("5100000"),
        tax_before_surcharge=Decimal("1400000"),
        regime="old",
        tax_at_threshold=Decimal("1300000")
    )

    # At ₹51 lakh, the maximum tax before cess is
    # ₹13 lakh + ₹1 lakh excess income = ₹14 lakh.
    assert result["surcharge"] == Decimal("0")


def test_negative_tax():
    with pytest.raises(ValueError):
        calculate_surcharge_and_cess(
            Decimal("6000000"),
            Decimal("-1000"),
            "old"
        )


def test_invalid_regime():
    with pytest.raises(ValueError):
        get_surcharge_details(
            Decimal("6000000"), "invalid"
        )



def test_exactly_50_lakh_has_no_surcharge():
    rate, threshold = get_surcharge_details(
        Decimal("5000000"), "old"
    )
    assert rate == Decimal("0")
    assert threshold == Decimal("0")


def test_exactly_1_crore_has_10_percent_surcharge():
    rate, threshold = get_surcharge_details(
        Decimal("10000000"), "old"
    )
    assert rate == Decimal("0.10")
    assert threshold == Decimal("5000000")


def test_exactly_2_crore_has_15_percent_surcharge():
    rate, threshold = get_surcharge_details(
        Decimal("20000000"), "old"
    )
    assert rate == Decimal("0.15")
    assert threshold == Decimal("10000000")


def test_exactly_5_crore_old_regime():
    rate, threshold = get_surcharge_details(
        Decimal("50000000"), "old"
    )
    assert rate == Decimal("0.25")
    assert threshold == Decimal("20000000")


def test_exactly_5_crore_new_regime():
    rate, threshold = get_surcharge_details(
        Decimal("50000000"), "new"
    )
    assert rate == Decimal("0.25")
    assert threshold == Decimal("20000000")


def test_above_5_crore_new_regime_stays_at_25_percent():
    rate, threshold = get_surcharge_details(
        Decimal("55000000"), "new"
    )
    assert rate == Decimal("0.25")
    assert threshold == Decimal("50000000")
