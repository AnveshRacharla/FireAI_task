from decimal import Decimal

HIGHER_LIMIT = Decimal("200000")
LOWER_LIMIT = Decimal("30000")


def calculate_24b_deduction(
    regime: str,
    annual_interest_paid: Decimal,
    qualifies_for_higher_limit: bool
) -> Decimal:

    if regime not in ("old", "new"):
        raise ValueError("Regime must be 'old' or 'new'")

    if annual_interest_paid < 0:
        raise ValueError("Interest cannot be negative")

    # No deduction for self-occupied property under the new regime.
    if regime == "new":
        return Decimal("0")

    limit = (
        HIGHER_LIMIT
        if qualifies_for_higher_limit
        else LOWER_LIMIT
    )

    return min(annual_interest_paid, limit)