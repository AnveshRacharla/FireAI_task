
import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

JSON_FILE = BASE_DIR / "numerical_test_cases.json"
CSV_FILE = BASE_DIR / "official_validation.csv"

CASE_IDS = [
    1, 9, 16, 24, 31, 39, 46, 54, 61, 69,
    77, 84, 92, 99, 107, 114, 122, 129, 137, 144,
    152, 160, 167, 175, 182, 190, 197, 205, 212, 220
]

FIELDS = [
    "case_id", "age", "gross_salary",
    "section_80c", "section_80ccd_1b",
    "section_80d_self", "section_80d_parents",
    "home_loan_interest", "regime",
    "our_tax", "official_tax", "difference", "status",
    "financial_year", "is_resident",
    "basic_salary", "dearness_allowance",
    "hra_received", "annual_rent_paid",
    "is_metro_city", "self_family_has_senior",
    "parents_are_senior_citizens",
    "qualifies_for_higher_24b_limit"
]

# Previously recorded official calculator values.
OFFICIAL_TAX = {
    (1, "old"): "2258260",
    (1, "new"): "2193620",
    (9, "old"): "65000",
    (9, "new"): "44200",
    (54, "old"): "171600",
    (54, "new"): "130000",
}


def main():
    with JSON_FILE.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    cases_by_id = {
        case["case_id"]: case["input"]
        for case in cases
    }

    rows = []

    for case_id in CASE_IDS:
        if case_id not in cases_by_id:
            raise ValueError(f"Missing case ID: {case_id}")

        original = cases_by_id[case_id].copy()

        for regime in ("old", "new"):
            data = original.copy()

            # Case 54 official calculator profile has no HRA claim.
            if case_id == 54:
                data.update({
                    "basic_salary": "0",
                    "dearness_allowance": "0",
                    "hra_received": "0",
                    "annual_rent_paid": "0",
                    "is_metro_city": False,
                })

            row = {
                "case_id": case_id,
                "age": data["age"],
                "gross_salary": data["annual_gross_salary"],
                "section_80c": data["section_80c_investment"],
                "section_80ccd_1b": data["section_80ccd_1b"],
                "section_80d_self": data["health_insurance_self_family"],
                "section_80d_parents": data["health_insurance_parents"],
                "home_loan_interest": data["home_loan_interest"],
                "regime": regime,
                "our_tax": "",
                "official_tax": OFFICIAL_TAX.get((case_id, regime), ""),
                "difference": "",
                "status": "PENDING",
                "financial_year": data["financial_year"],
                "is_resident": str(data["is_resident"]).lower(),
                "basic_salary": data["basic_salary"],
                "dearness_allowance": data["dearness_allowance"],
                "hra_received": data["hra_received"],
                "annual_rent_paid": data["annual_rent_paid"],
                "is_metro_city": str(data["is_metro_city"]).lower(),
                "self_family_has_senior": str(
                    data["self_family_has_senior"]
                ).lower(),
                "parents_are_senior_citizens": str(
                    data["parents_are_senior_citizens"]
                ).lower(),
                "qualifies_for_higher_24b_limit": str(
                    data["qualifies_for_higher_24b_limit"]
                ).lower(),
            }

            rows.append(row)

    with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Restored {len(rows)} rows.")
    print(f"Restored {len(CASE_IDS)} taxpayer profiles.")
    print(f"CSV: {CSV_FILE}")


if __name__ == "__main__":
    main()
