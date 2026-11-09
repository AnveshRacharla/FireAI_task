from decimal import Decimal

from project_a.tax_engine.regimes import get_tax_slabs
from project_a.tax_engine.slabs import calculate_slab_tax


def test_new_regime_slabs():
    slabs = get_tax_slabs("new", 25, True)

    tax = calculate_slab_tax(Decimal("700000"), slabs)

    assert tax == Decimal("20000.00")


def test_old_regime_below_60():
    slabs = get_tax_slabs("old", 25, True)

    tax = calculate_slab_tax(Decimal("700000"), slabs)

    assert tax == Decimal("52500.00")


def test_old_regime_senior_citizen():
    slabs = get_tax_slabs("old", 65, True)

    tax = calculate_slab_tax(Decimal("700000"), slabs)

    assert tax == Decimal("50000.00")


def test_old_regime_super_senior_citizen():
    slabs = get_tax_slabs("old", 82, True)

    tax = calculate_slab_tax(Decimal("700000"), slabs)

    assert tax == Decimal("40000.00")


def test_non_resident_uses_regular_old_slabs():
    slabs = get_tax_slabs("old", 65, False)

    tax = calculate_slab_tax(Decimal("700000"), slabs)

    assert tax == Decimal("52500.00")