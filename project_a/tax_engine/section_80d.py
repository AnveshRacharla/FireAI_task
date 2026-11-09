from decimal import Decimal

NON_SENIOR_LIMIT = Decimal("25000")
SENIOR_LIMIT = Decimal("50000")


def calculate_80d_deduction(
    regime: str,
    self_family_premium: Decimal,
    parents_premium: Decimal,
    self_family_has_senior: bool,
    parents_have_senior: bool
) -> Decimal:

    if regime not in ("old", "new"):
        raise ValueError("Regime must be 'old' or 'new'")

    amounts = [self_family_premium, parents_premium]

    if any(amount < 0 for amount in amounts):
        raise ValueError("Health insurance premium cannot be negative")

    if regime == "new":
        return Decimal("0")

    self_limit = (
        SENIOR_LIMIT if self_family_has_senior
        else NON_SENIOR_LIMIT
    )

    parents_limit = (
        SENIOR_LIMIT if parents_have_senior
        else NON_SENIOR_LIMIT
    )

    self_deduction = min(self_family_premium, self_limit)
    parents_deduction = min(parents_premium, parents_limit)

    return self_deduction + parents_deduction