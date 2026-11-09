
from decimal import Decimal


def calculate_hra_exemption(
    regime: str,
    basic_salary: Decimal,
    dearness_allowance: Decimal,
    hra_received: Decimal,
    annual_rent_paid: Decimal,
    is_metro_city: bool
) -> Decimal:

    if regime not in ("old", "new"):
        raise ValueError("Regime must be 'old' or 'new'")

    amounts = [
        basic_salary,
        dearness_allowance,
        hra_received,
        annual_rent_paid
    ]

    if any(amount < 0 for amount in amounts):
        raise ValueError("Salary, HRA and rent cannot be negative")

    # HRA exemption is not available under the new regime.
    if regime == "new":
        return Decimal("0")

    # Salary for HRA calculation.
    salary = basic_salary + dearness_allowance

    if salary == 0 or hra_received == 0 or annual_rent_paid == 0:
        return Decimal("0")

    # Condition 1: Actual HRA received.
    actual_hra = hra_received

    # Condition 2: Rent paid minus 10% of salary.
    rent_excess = max(
        Decimal("0"),
        annual_rent_paid - (salary * Decimal("0.10"))
    )

    # Condition 3: 50% for metro, 40% for non-metro.
    percentage = (
        Decimal("0.50")
        if is_metro_city
        else Decimal("0.40")
    )

    salary_percentage = salary * percentage

    # Exemption is the lowest of the three amounts.
    return min(
        actual_hra,
        rent_excess,
        salary_percentage
    )
