
import json
import random
from decimal import Decimal
from pathlib import Path

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.calculator import compare_regimes

random.seed(42)

SALARIES = [
    250000, 300000, 500000, 700000, 1000000,
    1200000, 1500000, 2000000, 3000000, 5000000,
    7500000, 10000000
]

AGES = [22, 25, 35, 45, 59, 60, 65, 75, 80, 85]


def generate_taxpayer():
    salary = random.choice(SALARIES)

    basic = Decimal(str(int(salary * 0.5)))
    hra = Decimal(str(int(salary * 0.2)))

    return {
        "financial_year": "2024-25",
        "annual_gross_salary": Decimal(str(salary)),
        "age": random.choice(AGES),
        "is_resident": True,

        "basic_salary": basic,
        "dearness_allowance": Decimal("0"),
        "hra_received": hra,
        "annual_rent_paid": Decimal(str(random.choice([
            0, 60000, 120000, 180000, 240000, 360000
        ]))),
        "is_metro_city": random.choice([True, False]),

        "section_80c_investment": Decimal(str(random.choice([
            0, 25000, 50000, 100000, 150000
        ]))),
        "section_80ccd_1b": Decimal(str(random.choice([
            0, 10000, 25000, 50000
        ]))),

        "health_insurance_self_family": Decimal(str(random.choice([
            0, 10000, 20000, 25000
        ]))),
        "health_insurance_parents": Decimal(str(random.choice([
            0, 10000, 25000, 50000
        ]))),
        "self_family_has_senior": False,
        "parents_are_senior_citizens": random.choice([True, False]),

        "home_loan_interest": Decimal(str(random.choice([
            0, 25000, 50000, 100000, 200000
        ]))),
        "qualifies_for_higher_24b_limit": True
    }


def main():
    cases = []

    for case_id in range(1, 221):
        taxpayer_data = generate_taxpayer()
        taxpayer = TaxpayerInput(**taxpayer_data)

        result = compare_regimes(taxpayer)

        cases.append({
            "case_id": case_id,
            "input": {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in taxpayer_data.items()
            },
            "expected_output": json.loads(
                json.dumps(result, default=str)
            )
        })

    output = Path("project_a/data/numerical_test_cases.json")

    with output.open("w", encoding="utf-8") as file:
        json.dump(cases, file, indent=4)

    print("Generated cases:", len(cases))
    print("Saved to:", output)


if __name__ == "__main__":
    main()
