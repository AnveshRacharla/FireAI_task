
import csv
from collections import Counter
from pathlib import Path

CSV_FILE = Path(__file__).parent / "official_validation.csv"


def main():
    with CSV_FILE.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    counts = Counter(row["status"] for row in rows)

    verified = [
        row for row in rows
        if row["official_tax"].strip()
    ]

    print("\n========== OFFICIAL VALIDATION SUMMARY ==========")
    print(f"Total comparisons: {len(rows)}")
    print(f"Official values entered: {len(verified)}")
    print(f"PASS: {counts['PASS']}")
    print(f"FAIL: {counts['FAIL']}")
    print(f"PENDING: {counts['PENDING']}")

    print("\nMISMATCHES:")
    for row in rows:
        if row["status"] == "FAIL":
            print(
                f"Case {row['case_id']} | {row['regime']} | "
                f"Our: {row['our_tax']} | "
                f"Official: {row['official_tax']} | "
                f"Difference: {row['difference']}"
            )


if __name__ == "__main__":
    main()
