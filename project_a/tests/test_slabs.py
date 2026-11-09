
from decimal import Decimal

from project_a.tax_engine.slabs import (
    TaxSlab,
    calculate_slab_tax
)


SLABS = [
    TaxSlab(Decimal("0"), Decimal("300000"), Decimal("0")),
    TaxSlab(Decimal("300000"), Decimal("600000"), Decimal("0.05")),
    TaxSlab(Decimal("600000"), Decimal("900000"), Decimal("0.10")),
]


def test_tax_on_seven_lakhs():
    result = calculate_slab_tax(Decimal("700000"), SLABS)
    assert result == Decimal("25000.00")


def test_tax_below_first_slab():
    result = calculate_slab_tax(Decimal("200000"), SLABS)
    assert result == Decimal("0")


def test_tax_at_slab_boundary():
    result = calculate_slab_tax(Decimal("600000"), SLABS)
    assert result == Decimal("15000.00")


def test_negative_income():
    import pytest

    with pytest.raises(ValueError):
        calculate_slab_tax(Decimal("-1000"), SLABS)
