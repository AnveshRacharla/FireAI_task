from project_a.schemas.taxpayer import TaxpayerInput
from project_a.implementations.rules_based import calculate_tax_rules_based


def test_rules_based_calculation():
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
        qualifies_for_higher_24b_limit=False,
    )

    result = calculate_tax_rules_based(taxpayer)

    assert "old_regime" in result
    assert "new_regime" in result
    assert "recommended_regime" in result