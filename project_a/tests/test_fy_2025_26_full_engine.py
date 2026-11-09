
from decimal import Decimal

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.calculator import calculate_regime_tax


def make_taxpayer(salary):
    return TaxpayerInput(
        financial_year="2025-26",
        annual_gross_salary=salary,
        age=25,
        is_resident=True
    )


def test_full_engine_rebate_at_12_lakh():
    taxpayer = make_taxpayer(1275000)

    result = calculate_regime_tax(taxpayer, "new")

    assert result["taxable_income"] == Decimal("1200000")
    assert result["tax_before_rebate"] == Decimal("60000")
    assert result["rebate_87a"] == Decimal("60000")
    assert result["total_tax"] == Decimal("0")


def test_full_engine_marginal_relief():
    taxpayer = make_taxpayer(1285000)

    result = calculate_regime_tax(taxpayer, "new")

    assert result["taxable_income"] == Decimal("1210000")
    assert result["tax_before_rebate"] == Decimal("61500")
    assert result["rebate_87a"] == Decimal("51500")
    assert result["tax_after_rebate"] == Decimal("10000")
    assert result["total_tax"] == Decimal("10400")


def test_full_engine_old_regime_still_works():
    taxpayer = TaxpayerInput(
        financial_year="2025-26",
        annual_gross_salary=1200000,
        age=25,
        is_resident=True,
        section_80c_investment=0,
        section_80ccd_1b=0,
        health_insurance_self_family=0,
        health_insurance_parents=0,
        self_family_has_senior=False,
        parents_are_senior_citizens=False
    )

    result = calculate_regime_tax(taxpayer, "old")

    assert result["standard_deduction"] == Decimal("50000")
    assert result["taxable_income"] == Decimal("1150000")