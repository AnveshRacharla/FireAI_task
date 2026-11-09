
from decimal import Decimal


def calculate_standard_deduction(
    gross_salary: Decimal,
    regime: str
) -> Decimal:

    if gross_salary < 0:
        raise ValueError("Gross salary cannot be negative")

    if regime == "old":
        limit = Decimal("50000")

    elif regime == "new":
        limit = Decimal("75000")

    else:
        raise ValueError("Regime must be 'old' or 'new'")

    return min(gross_salary, limit)
