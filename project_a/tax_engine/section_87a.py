
from decimal import Decimal

ZERO = Decimal("0")


def calculate_87a_rebate(
    regime: str,
    taxable_income: Decimal,
    tax_before_rebate: Decimal,
    financial_year: str = "2024-25",
    is_resident: bool = True
) -> Decimal:

    if regime not in ("old", "new"):
        raise ValueError("Invalid tax regime")

    if financial_year not in ("2024-25", "2025-26"):
        raise ValueError("Unsupported financial year")

    if taxable_income < ZERO or tax_before_rebate < ZERO:
        raise ValueError("Income and tax cannot be negative")

    if not is_resident:
        return ZERO

    if regime == "old":
        if taxable_income <= Decimal("500000"):
            return min(tax_before_rebate, Decimal("12500"))
        return ZERO

    if financial_year == "2024-25":
        if taxable_income <= Decimal("700000"):
            return min(tax_before_rebate, Decimal("25000"))
        return ZERO

    # FY 2025-26: New regime
    threshold = Decimal("1200000")
    rebate_limit = Decimal("60000")

    if taxable_income <= threshold:
        return min(tax_before_rebate, rebate_limit)

    # Marginal relief above Rs. 12 lakh
    excess_income = taxable_income - threshold

    marginal_relief = max(
        ZERO,
        tax_before_rebate - excess_income
    )

    return min(
        tax_before_rebate,
        rebate_limit,
        marginal_relief
    )
