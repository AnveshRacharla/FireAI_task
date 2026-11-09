
from decimal import Decimal

from project_a.tax_engine.slabs import TaxSlab


def get_tax_slabs(
    regime: str,
    age: int,
    is_resident: bool,
    financial_year: str = "2024-25"
) -> list[TaxSlab]:

    if regime not in ("old", "new"):
        raise ValueError("Invalid tax regime")

    if financial_year not in ("2024-25", "2025-26"):
        raise ValueError("Unsupported financial year")

    # New regime: FY 2024-25
    if regime == "new" and financial_year == "2024-25":
        return [
            TaxSlab(Decimal("0"), Decimal("300000"), Decimal("0")),
            TaxSlab(Decimal("300000"), Decimal("700000"), Decimal("0.05")),
            TaxSlab(Decimal("700000"), Decimal("1000000"), Decimal("0.10")),
            TaxSlab(Decimal("1000000"), Decimal("1200000"), Decimal("0.15")),
            TaxSlab(Decimal("1200000"), Decimal("1500000"), Decimal("0.20")),
            TaxSlab(Decimal("1500000"), None, Decimal("0.30")),
        ]

    # New regime: FY 2025-26
    if regime == "new" and financial_year == "2025-26":
        return [
            TaxSlab(Decimal("0"), Decimal("400000"), Decimal("0")),
            TaxSlab(Decimal("400000"), Decimal("800000"), Decimal("0.05")),
            TaxSlab(Decimal("800000"), Decimal("1200000"), Decimal("0.10")),
            TaxSlab(Decimal("1200000"), Decimal("1600000"), Decimal("0.15")),
            TaxSlab(Decimal("1600000"), Decimal("2000000"), Decimal("0.20")),
            TaxSlab(Decimal("2000000"), Decimal("2400000"), Decimal("0.25")),
            TaxSlab(Decimal("2400000"), None, Decimal("0.30")),
        ]

    # Old regime: same slabs for both financial years
    if regime == "old":

        if is_resident and age >= 80:
            return [
                TaxSlab(Decimal("0"), Decimal("500000"), Decimal("0")),
                TaxSlab(Decimal("500000"), Decimal("1000000"), Decimal("0.20")),
                TaxSlab(Decimal("1000000"), None, Decimal("0.30")),
            ]

        if is_resident and age >= 60:
            return [
                TaxSlab(Decimal("0"), Decimal("300000"), Decimal("0")),
                TaxSlab(Decimal("300000"), Decimal("500000"), Decimal("0.05")),
                TaxSlab(Decimal("500000"), Decimal("1000000"), Decimal("0.20")),
                TaxSlab(Decimal("1000000"), None, Decimal("0.30")),
            ]

        return [
            TaxSlab(Decimal("0"), Decimal("250000"), Decimal("0")),
            TaxSlab(Decimal("250000"), Decimal("500000"), Decimal("0.05")),
            TaxSlab(Decimal("500000"), Decimal("1000000"), Decimal("0.20")),
            TaxSlab(Decimal("1000000"), None, Decimal("0.30")),
        ]

    raise ValueError("Unsupported tax regime or financial year")
