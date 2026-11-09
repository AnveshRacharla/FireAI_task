
from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.calculator import calculate_regime_tax
from project_a.implementations.compiled_rules import calculate_compiled_regime_tax


def test_compiled_engine_matches_rules_engine():

    taxpayer = TaxpayerInput(
        financial_year="2024-25",
        annual_gross_salary=1200000,
        age=25,
        is_resident=True,

        # No HRA details supplied
        section_80c_investment=0,
        section_80ccd_1b=0,

        # Section 80D: explicitly provide zero values
        health_insurance_self_family=0,
        health_insurance_parents=0,
        self_family_has_senior=False,
        parents_are_senior_citizens=False,

        # # No home loan
        # home_loan_interest=0
    )

    for regime in ["old", "new"]:

        original = calculate_regime_tax(taxpayer, regime)

        compiled = calculate_compiled_regime_tax(
            taxpayer, regime
        )

        assert compiled["total_tax"] == original["total_tax"]
        assert compiled["taxable_income"] == original["taxable_income"]
