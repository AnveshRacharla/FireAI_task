import json
from decimal import Decimal
from pathlib import Path

from project_a.tax_engine.calculator import calculate_regime_tax
from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.slabs import TaxSlab, calculate_slab_tax

RULES_PATH = Path("project_a/data/compiled_tax_rules.json")

ZERO = Decimal("0")


def load_compiled_rules():
    with RULES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def convert_to_slabs(rule_list):
    return [
        TaxSlab(
            lower_limit=Decimal(str(rule["lower"])),
            upper_limit=(
                Decimal(str(rule["upper"]))
                if rule["upper"] is not None else None
            ),
            rate=Decimal(str(rule["rate"]))
        )
        for rule in rule_list
    ]


def select_rules(rules, financial_year, regime, age):
    if financial_year not in rules:
        raise ValueError("Unsupported financial year")

    year_rules = rules[financial_year]

    if regime == "new":
        return year_rules["new_regime"]

    if regime == "old":
        if age >= 80:
            return year_rules["old_regime"]["super_senior_80_plus"]
        elif age >= 60:
            return year_rules["old_regime"]["senior_60_to_79"]
        else:
            return year_rules["old_regime"]["below_60"]

    raise ValueError("Regime must be 'old' or 'new'")


def calculate_compiled_tax(
    taxable_income,
    regime,
    age,
    financial_year="2024-25"
):
    """
    Standalone slab-level calculation.
    Assumes the taxpayer is resident.
    Does not include deductions or surcharge.
    """
    taxable_income = Decimal(str(taxable_income))
    rules = load_compiled_rules()

    selected_rules = select_rules(
        rules, financial_year, regime, age
    )

    slabs = convert_to_slabs(selected_rules)
    tax = calculate_slab_tax(taxable_income, slabs)

    rebate = ZERO

    if regime == "old" and taxable_income <= Decimal("500000"):
        rebate = min(tax, Decimal("12500"))

    elif regime == "new" and financial_year == "2024-25":
        if taxable_income <= Decimal("700000"):
            rebate = min(tax, Decimal("25000"))

    elif regime == "new" and financial_year == "2025-26":
        threshold = Decimal("1200000")
        rebate_limit = Decimal("60000")

        if taxable_income <= threshold:
            rebate = min(tax, rebate_limit)
        else:
            excess_income = taxable_income - threshold
            marginal_relief = max(ZERO, tax - excess_income)
            rebate = min(tax, rebate_limit, marginal_relief)

    tax_after_rebate = max(ZERO, tax - rebate)
    cess = tax_after_rebate * Decimal("0.04")
    total_tax = tax_after_rebate + cess

    return {
        "tax_before_rebate": tax,
        "rebate": rebate,
        "tax_after_rebate": tax_after_rebate,
        "cess": cess,
        "total_tax": total_tax
    }


def calculate_compiled_regime_tax(
    taxpayer: TaxpayerInput,
    regime: str
) -> dict:

    rules = load_compiled_rules()

    selected_rules = select_rules(
        rules,
        taxpayer.financial_year,
        regime,
        taxpayer.age
    )

    slabs = convert_to_slabs(selected_rules)

    return calculate_regime_tax(
        taxpayer,
        regime,
        slab_override=slabs
    )