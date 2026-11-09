from decimal import Decimal

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.implementations.compiled_rules import (
    calculate_compiled_regime_tax,
    calculate_compiled_tax
)
from project_a.tax_engine.calculator import calculate_regime_tax


def make_taxpayer(salary, financial_year="2025-26"):
    return TaxpayerInput(
        financial_year=financial_year,
        annual_gross_salary=salary,
        age=25,
        is_resident=True,
        section_80c_investment=0,
        section_80ccd_1b=0,
        health_insurance_self_family=0,
        health_insurance_parents=0,
        self_family_has_senior=False,
        parents_are_senior_citizens=False
    )


def test_compiled_fy_2025_26_new_regime_slabs():
    result = calculate_compiled_tax(
        taxable_income=1200000,
        regime="new",
        age=25,
        financial_year="2025-26"
    )

    assert result["tax_before_rebate"] == Decimal("60000")
    assert result["rebate"] == Decimal("60000")
    assert result["total_tax"] == Decimal("0")


def test_compiled_engine_matches_rules_engine_fy_2025_26():
    taxpayer = make_taxpayer(1285000)

    compiled = calculate_compiled_regime_tax(taxpayer, "new")
    rules = calculate_regime_tax(taxpayer, "new")

    assert compiled == rules


def test_compiled_engine_matches_rules_engine_fy_2024_25():
    taxpayer = make_taxpayer(1275000, "2024-25")

    compiled = calculate_compiled_regime_tax(taxpayer, "new")
    rules = calculate_regime_tax(taxpayer, "new")

    assert compiled == rules


def test_compiled_fy_2025_26_marginal_relief():
    result = calculate_compiled_tax(
        taxable_income=1210000,
        regime="new",
        age=25,
        financial_year="2025-26"
    )

    assert result["tax_before_rebate"] == Decimal("61500")
    assert result["rebate"] == Decimal("51500")
    assert result["tax_after_rebate"] == Decimal("10000")