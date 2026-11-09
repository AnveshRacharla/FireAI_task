
from decimal import Decimal


SECTION_80C_LIMIT = Decimal("150000")


def calculate_80c_deduction(
    regime: str,
    eligible_investment: Decimal
) -> Decimal:

    if regime not in ("old", "new"):
        raise ValueError("Regime must be 'old' or 'new'")

    if eligible_investment < 0:
        raise ValueError("Investment cannot be negative")

    # Section 80C is not available in the new regime.
    if regime == "new":
        return Decimal("0")

    # Deduction cannot exceed the statutory limit.
    return min(eligible_investment, SECTION_80C_LIMIT)
