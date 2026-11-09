import json
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "numerical_test_cases.json"
OUTPUT_FILE = BASE_DIR / "official_validation.csv"

with INPUT_FILE.open("r", encoding="utf-8") as file:
    cases = json.load(file)

# Select 30 evenly distributed cases from the 220 profiles.
selected = [
    cases[round(i * (len(cases) - 1) / 29)]
    for i in range(30)
]

columns = [
    "case_id",
    "age",
    "gross_salary",
    "section_80c",
    "section_80ccd_1b",
    "section_80d_self",
    "section_80d_parents",
    "home_loan_interest",
    "regime",
    "our_tax",
    "official_tax",
    "difference",
    "status"
]

with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()

    for case in selected:
        data = case["input"]
        expected = case["expected_output"]

        for regime in ["old", "new"]:
            result = expected[f"{regime}_regime"]

            writer.writerow({
                "case_id": case["case_id"],
                "age": data["age"],
                "gross_salary": data["annual_gross_salary"],
                "section_80c": data.get("section_80c_investment", 0),
                "section_80ccd_1b": data.get("section_80ccd_1b", 0),
                "section_80d_self": data.get("health_insurance_self_family", 0),
                "section_80d_parents": data.get("health_insurance_parents", 0),
                "home_loan_interest": data.get("home_loan_interest", 0),
                "regime": regime,
                "our_tax": result["total_tax"],
                "official_tax": "",
                "difference": "",
                "status": "PENDING"
            })

print(f"Created {OUTPUT_FILE}")
print(f"Selected {len(selected)} taxpayer profiles.")
print(f"Created {len(selected) * 2} regime comparisons.")