
from decimal import Decimal

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.slabs import calculate_slab_tax
from project_a.tax_engine.regimes import get_tax_slabs
from project_a.tax_engine.deductions import calculate_standard_deduction
from project_a.tax_engine.hra import calculate_hra_exemption
from project_a.tax_engine.section_80c import calculate_80c_deduction
from project_a.tax_engine.section_80ccd import calculate_80ccd_1b_deduction
from project_a.tax_engine.section_80d import calculate_80d_deduction
from project_a.tax_engine.section_24b import calculate_24b_deduction
from project_a.tax_engine.section_87a import calculate_87a_rebate
from project_a.tax_engine.surcharge_cess import (
    calculate_surcharge_and_cess,
    get_surcharge_details
)
from project_a.tax_engine.rounding import (
    round_taxable_income,
    round_tax_payable,
)

ZERO = Decimal("0")
CESS_RATE = Decimal("0.04")


def calculate_regime_tax(
    taxpayer: TaxpayerInput,
    regime: str,
    slab_override=None
) -> dict:

    if taxpayer.financial_year not in ("2024-25", "2025-26"):
        raise ValueError("Unsupported financial year")

    # Validate HRA information when any HRA detail is supplied.
    hra_fields = [
        taxpayer.basic_salary,
        taxpayer.dearness_allowance,
        taxpayer.hra_received,
        taxpayer.annual_rent_paid,
        taxpayer.is_metro_city
    ]

    if any(value is not None for value in hra_fields):
        if any(value is None for value in hra_fields):
            raise ValueError("Complete all HRA details or provide none")

        hra_exemption = calculate_hra_exemption(
            regime,
            taxpayer.basic_salary,
            taxpayer.dearness_allowance,
            taxpayer.hra_received,
            taxpayer.annual_rent_paid,
            taxpayer.is_metro_city
        )
    else:
        hra_exemption = ZERO

    standard_deduction = calculate_standard_deduction(
        taxpayer.annual_gross_salary, regime
    )

    deduction_80c = calculate_80c_deduction(
        regime, taxpayer.section_80c_investment or ZERO
    )

    deduction_80ccd = calculate_80ccd_1b_deduction(
        regime, taxpayer.section_80ccd_1b or ZERO
    )

    # Section 80D requires both category amounts and senior status.
    if (
        taxpayer.health_insurance_self_family is None
        or taxpayer.health_insurance_parents is None
        or taxpayer.self_family_has_senior is None
        or taxpayer.parents_are_senior_citizens is None
    ):
        if regime == "old":
            raise ValueError("Provide complete Section 80D details, using zero where not applicable")
        deduction_80d = ZERO
    else:
        deduction_80d = calculate_80d_deduction(
            regime,
            taxpayer.health_insurance_self_family,
            taxpayer.health_insurance_parents,
            taxpayer.self_family_has_senior,
            taxpayer.parents_are_senior_citizens
        )

    # Section 24(b): self-occupied home loan.
    if taxpayer.home_loan_interest is None:
        deduction_24b = ZERO
    elif taxpayer.qualifies_for_higher_24b_limit is None:
        raise ValueError("Specify whether the loan qualifies for the higher Section 24(b) limit")
    else:
        deduction_24b = calculate_24b_deduction(
            regime,
            taxpayer.home_loan_interest,
            taxpayer.qualifies_for_higher_24b_limit
        )

    total_deductions = (
        standard_deduction
        + hra_exemption
        + deduction_80c
        + deduction_80ccd
        + deduction_80d
        + deduction_24b
    )

    taxable_income = max(
        ZERO,
        taxpayer.annual_gross_salary - total_deductions
    )

    taxable_income = round_taxable_income(taxable_income)
    
    if slab_override is None:
        slabs = get_tax_slabs(
            regime,
            taxpayer.age,
            taxpayer.is_resident,
            taxpayer.financial_year
        )
    else:
        slabs = slab_override

    
    tax_before_rebate = calculate_slab_tax(taxable_income, slabs)

    rebate = calculate_87a_rebate(
        regime,
        taxable_income,
        tax_before_rebate,
        taxpayer.financial_year,
        taxpayer.is_resident
    )

    tax_after_rebate = max(
        ZERO,
        tax_before_rebate - rebate
    )

    # Find the surcharge threshold currently crossed.
    surcharge_rate, threshold = get_surcharge_details(
        taxable_income,
        regime
    )

    # Calculate tax liability at that exact threshold.
    if surcharge_rate > ZERO:
        tax_at_threshold = calculate_slab_tax(
            threshold,
            slabs
        )

        threshold_rate, _ = get_surcharge_details(
            threshold,
            regime
        )

        tax_at_threshold += tax_at_threshold * threshold_rate
    else:
        tax_at_threshold = ZERO

    # Apply surcharge and marginal relief.
    surcharge_result = calculate_surcharge_and_cess(
        taxable_income=taxable_income,
        tax_before_surcharge=tax_after_rebate,
        regime=regime,
        tax_at_threshold=tax_at_threshold
    )

    surcharge = surcharge_result["surcharge"]
    cess = surcharge_result["cess"]

    total_tax = round_tax_payable(
        surcharge_result["total_tax"]
    )

    return {
        "regime": regime,
        "gross_salary": taxpayer.annual_gross_salary,
        "standard_deduction": standard_deduction,
        "hra_exemption": hra_exemption,
        "section_80c": deduction_80c,
        "section_80ccd_1b": deduction_80ccd,
        "section_80d": deduction_80d,
        "section_24b": deduction_24b,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate_87a": rebate,
        "tax_after_rebate": tax_after_rebate,
        "cess": cess,
        "surcharge": surcharge,
        "surcharge_rate": surcharge_result["surcharge_rate"],
        "total_tax": total_tax
        
    }


def compare_regimes(taxpayer: TaxpayerInput) -> dict:
    old_result = calculate_regime_tax(taxpayer, "old")
    new_result = calculate_regime_tax(taxpayer, "new")

    recommended = (
        "old"
        if old_result["total_tax"] < new_result["total_tax"]
        else "new"
    )

    return {
        "old_regime": old_result,
        "new_regime": new_result,
        "recommended_regime": recommended,
        "tax_savings": abs(
            old_result["total_tax"] - new_result["total_tax"]
        )
    }
