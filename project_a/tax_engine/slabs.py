
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class TaxSlab:
    lower_limit: Decimal
    upper_limit: Optional[Decimal]
    rate: Decimal


def calculate_slab_tax(
    taxable_income: Decimal,
    slabs: list[TaxSlab]
) -> Decimal:

    if taxable_income < 0:
        raise ValueError("Taxable income cannot be negative")

    total_tax = Decimal("0")

    for slab in slabs:
        if taxable_income <= slab.lower_limit:
            continue

        upper_limit = (
            slab.upper_limit
            if slab.upper_limit is not None
            else taxable_income
        )

        taxable_amount = min(taxable_income, upper_limit) - slab.lower_limit

        if taxable_amount > 0:
            total_tax += taxable_amount * slab.rate

    return total_tax
