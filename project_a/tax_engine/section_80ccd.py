from decimal import Decimal

SECTION_80CCD_1B_LIMIT = Decimal("50000")


def calculate_80ccd_1b_deduction(
    regime: str,
    eligible_nps_contribution: Decimal
) -> Decimal:

    if regime not in ("old", "new"):
        raise ValueError("Regime must be 'old' or 'new'")

    if eligible_nps_contribution < 0:
        raise ValueError("NPS contribution cannot be negative")

    # This deduction is not available under the new regime.
    if regime == "new":
        return Decimal("0")

    return min(
        eligible_nps_contribution,
        SECTION_80CCD_1B_LIMIT
    )