from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

TEN = Decimal("10")
ONE = Decimal("1")


def round_taxable_income(amount: Decimal) -> Decimal:
    # Ignore paise first, then round to nearest ₹10.
    whole_rupees = amount.quantize(ONE, rounding=ROUND_DOWN)
    return (whole_rupees / TEN).quantize(
        ONE, rounding=ROUND_HALF_UP
    ) * TEN


def round_tax_payable(amount: Decimal) -> Decimal:
    # Ignore paise first, then round to nearest ₹10.
    whole_rupees = amount.quantize(ONE, rounding=ROUND_DOWN)
    return (whole_rupees / TEN).quantize(
        ONE, rounding=ROUND_HALF_UP
    ) * TEN
    