from decimal import Decimal

ZERO = Decimal("0")
CESS_RATE = Decimal("0.04")


def get_surcharge_details(
    taxable_income: Decimal,
    regime: str
) -> tuple[Decimal, Decimal]:

    if regime not in ("old", "new"):
        raise ValueError("Regime must be 'old' or 'new'")

    if taxable_income < ZERO:
        raise ValueError("Taxable income cannot be negative")

    if taxable_income <= Decimal("5000000"):
        return ZERO, ZERO

    if taxable_income <= Decimal("10000000"):
        return Decimal("0.10"), Decimal("5000000")

    if taxable_income <= Decimal("20000000"):
        return Decimal("0.15"), Decimal("10000000")

    if taxable_income <= Decimal("50000000"):
        return Decimal("0.25"), Decimal("20000000")

    if regime == "new":
        return Decimal("0.25"), Decimal("50000000")

    return Decimal("0.37"), Decimal("50000000")


def calculate_surcharge_and_cess(
    taxable_income: Decimal,
    tax_before_surcharge: Decimal,
    regime: str,
    tax_at_threshold: Decimal = ZERO
) -> dict:

    if tax_before_surcharge < ZERO or tax_at_threshold < ZERO:
        raise ValueError("Tax amounts cannot be negative")

    rate, threshold = get_surcharge_details(
        taxable_income, regime
    )

    normal_surcharge = tax_before_surcharge * rate

    surcharge = normal_surcharge

    if rate > ZERO:
        maximum_tax_with_surcharge = (
            tax_at_threshold + taxable_income - threshold
        )

        maximum_surcharge = max(
            ZERO,
            maximum_tax_with_surcharge - tax_before_surcharge
        )

        surcharge = min(normal_surcharge, maximum_surcharge)

    tax_after_surcharge = tax_before_surcharge + surcharge

    cess = tax_after_surcharge * CESS_RATE

    total_tax = tax_after_surcharge + cess

    return {
        "surcharge_rate": rate,
        "surcharge": surcharge,
        "tax_after_surcharge": tax_after_surcharge,
        "cess": cess,
        "total_tax": total_tax
    }