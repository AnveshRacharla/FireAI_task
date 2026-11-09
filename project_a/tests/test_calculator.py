
from decimal import Decimal

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.calculator import compare_regimes

def test_no_surcharge_for_income_below_50_lakh():
    taxpayer = TaxpayerInput(
        annual_gross_salary=1200000,
        age=25,
        is_resident=True,
        section_80c_investment=0,
        section_80ccd_1b=0,
        health_insurance_self_family=0,
        health_insurance_parents=0,
        self_family_has_senior=False,
        parents_are_senior_citizens=False,
        home_loan_interest=0,
        qualifies_for_higher_24b_limit=False
    )

    result = compare_regimes(taxpayer)

    assert result["old_regime"]["surcharge"] == Decimal("0")
    assert result["new_regime"]["surcharge"] == Decimal("0")

def test_compare_old_and_new_regimes():
    taxpayer = TaxpayerInput(
        annual_gross_salary=1200000,
        age=25,
        is_resident=True,

        section_80c_investment=0,
        section_80ccd_1b=0,

        health_insurance_self_family=0,
        health_insurance_parents=0,
        self_family_has_senior=False,
        parents_are_senior_citizens=False,

        home_loan_interest=0,
        qualifies_for_higher_24b_limit=False
    )

    result = compare_regimes(taxpayer)

    assert result["old_regime"]["taxable_income"] == Decimal("1150000")
    assert result["new_regime"]["taxable_income"] == Decimal("1125000")
    assert result["recommended_regime"] == "new"
    assert result["old_regime"]["total_tax"] == Decimal("163800.0000")
    assert result["new_regime"]["total_tax"] == Decimal("71500.0000")

