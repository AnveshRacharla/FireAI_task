
from decimal import Decimal

from project_a.tax_engine.regimes import get_tax_slabs
from project_a.tax_engine.slabs import calculate_slab_tax
from project_a.tax_engine.section_87a import calculate_87a_rebate
from project_a.tax_engine.deductions import calculate_standard_deduction


def test_new_regime_slabs_fy_2025_26():
    slabs = get_tax_slabs("new", 25, True, "2025-26")

    assert len(slabs) == 7
    assert slabs[0].upper_limit == Decimal("400000")
    assert slabs[-1].lower_limit == Decimal("2400000")


def test_new_regime_tax_at_12_lakh():
    slabs = get_tax_slabs("new", 25, True, "2025-26")

    tax = calculate_slab_tax(Decimal("1200000"), slabs)

    assert tax == Decimal("60000")


def test_rebate_at_12_lakh():
    rebate = calculate_87a_rebate(
        "new", Decimal("1200000"), Decimal("60000"), "2025-26"
    )

    assert rebate == Decimal("60000")


def test_marginal_relief_above_12_lakh():
    rebate = calculate_87a_rebate(
        "new", Decimal("1210000"), Decimal("61500"), "2025-26"
    )

    assert rebate == Decimal("51500")
    assert Decimal("61500") - rebate == Decimal("10000")


def test_no_rebate_for_non_resident():
    rebate = calculate_87a_rebate(
        "new", Decimal("1000000"), Decimal("45000"),
        "2025-26", False
    )

    assert rebate == Decimal("0")


def test_standard_deduction_fy_2025_26():
    deduction = calculate_standard_deduction(
        Decimal("1500000"), "new"
    )

    assert deduction == Decimal("75000")


def test_old_regime_slabs_unchanged():
    old_slabs = get_tax_slabs("old", 25, True, "2024-25")
    new_year_old_slabs = get_tax_slabs("old", 25, True, "2025-26")

    assert old_slabs == new_year_old_slabs
