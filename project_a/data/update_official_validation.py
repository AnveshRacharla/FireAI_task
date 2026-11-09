
import csv
from decimal import Decimal
from pathlib import Path

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.calculator import calculate_regime_tax

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "official_validation.csv"

# Every taxpayer input must be recorded in the validation CSV.
REQUIRED_INPUTS = [
    "financial_year",
    "is_resident",
    "basic_salary",
    "dearness_allowance",
    "hra_received",
    "annual_rent_paid",
    "is_metro_city",
    "self_family_has_senior",
    "parents_are_senior_citizens",
    "qualifies_for_higher_24b_limit",
]

DECIMAL_FIELDS = [
    "gross_salary",
    "section_80c",
    "section_80ccd_1b",
    "section_80d_self",
    "section_80d_parents",
    "home_loan_interest",
    "basic_salary",
    "dearness_allowance",
    "hra_received",
    "annual_rent_paid",
]

BOOLEAN_FIELDS = [
    "is_resident",
    "is_metro_city",
    "self_family_has_senior",
    "parents_are_senior_citizens",
    "qualifies_for_higher_24b_limit",
]


def parse_bool(value, field, case_id):
    value = value.strip().lower()

    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False

    raise ValueError(
        f"Case {case_id}: invalid or missing {field}: {value!r}"
    )


def build_taxpayer(row):
    case_id = row["case_id"]

    for field in REQUIRED_INPUTS:
        if not row.get(field, "").strip():
            raise ValueError(
                f"Case {case_id}: missing required input '{field}'."
            )

    data = {
        "financial_year": row["financial_year"].strip(),
        "annual_gross_salary": Decimal(row["gross_salary"]),
        "age": int(row["age"]),
        "section_80c_investment": Decimal(row["section_80c"]),
        "section_80ccd_1b": Decimal(row["section_80ccd_1b"]),
        "health_insurance_self_family": Decimal(row["section_80d_self"]),
        "health_insurance_parents": Decimal(row["section_80d_parents"]),
        "home_loan_interest": Decimal(row["home_loan_interest"]),
    }

    for field in DECIMAL_FIELDS[6:]:
        data[field] = Decimal(row[field])

    for field in BOOLEAN_FIELDS:
        data[field] = parse_bool(row[field], field, case_id)

    return TaxpayerInput(**data)


def main():
    with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise ValueError("CSV header is missing.")

    missing_columns = [
        field for field in REQUIRED_INPUTS
        if field not in fieldnames
    ]

    if missing_columns:
        raise ValueError(
            "Add these columns to official_validation.csv: "
            + ", ".join(missing_columns)
        )

    for row in rows:
        taxpayer = build_taxpayer(row)

        regime = row["regime"].strip().lower()

        if regime not in ("old", "new"):
            raise ValueError(
                f"Case {row['case_id']}: invalid regime {regime}"
            )

        result = calculate_regime_tax(taxpayer, regime)
        our_tax = result["total_tax"]

        row["our_tax"] = format(our_tax, "f")

        official_value = row["official_tax"].strip()

        if official_value:
            difference = our_tax - Decimal(official_value)
            row["difference"] = format(difference, "f")
            row["status"] = "PASS" if difference == 0 else "FAIL"
        else:
            row["difference"] = ""
            row["status"] = "PENDING"

    with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {len(rows)} validation rows.")
    print("Official tax values preserved.")
    print("Source: official_validation.csv")


if __name__ == "__main__":
    main()
