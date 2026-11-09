
from decimal import Decimal

from project_a.tax_engine.slabs import (
    TaxSlab,
    calculate_slab_tax
)


def test_tax_at_zero():
    assert calculate_slab_tax(
        Decimal("0"),
        [TaxSlab(Decimal("0"), None, Decimal("0.10"))]
    ) == Decimal("0")


def test_tax_at_slab_boundary():
    slabs = [
        TaxSlab(Decimal("0"), Decimal("300000"), Decimal("0")),
        TaxSlab(Decimal("300000"), Decimal("600000"), Decimal("0.05"))
    ]

    assert calculate_slab_tax(Decimal("300000"), slabs) == Decimal("0")


def test_tax_just_above_slab_boundary():
    slabs = [
        TaxSlab(Decimal("0"), Decimal("300000"), Decimal("0")),
        TaxSlab(Decimal("300000"), Decimal("600000"), Decimal("0.05"))
    ]

    assert calculate_slab_tax(Decimal("300001"), slabs) == Decimal("0.05")


def test_tax_at_upper_slab_boundary():
    slabs = [
        TaxSlab(Decimal("0"), Decimal("300000"), Decimal("0")),
        TaxSlab(Decimal("300000"), Decimal("600000"), Decimal("0.05"))
    ]

    assert calculate_slab_tax(Decimal("600000"), slabs) == Decimal("15000")
