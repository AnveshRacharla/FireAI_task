from decimal import Decimal
from project_a.tax_engine.regimes import get_tax_slabs
from project_a.tax_engine.slabs import calculate_slab_tax


def test_fy_2024_25_new_regime_correct_slabs():
    slabs = get_tax_slabs("new", 25, True, "2024-25")

    assert slabs[1].upper_limit == Decimal("700000")
    assert slabs[2].upper_limit == Decimal("1000000")


def test_fy_2024_25_tax_at_925000():
    slabs = get_tax_slabs("new", 25, True, "2024-25")

    tax = calculate_slab_tax(Decimal("925000"), slabs)

    assert tax == Decimal("42500")