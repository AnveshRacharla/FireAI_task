import csv
from pathlib import Path
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "official_validation.csv"

matched = 0
completed = 0
differences = []

with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

for row in rows:
    if not row["official_tax"].strip():
        continue

    our_tax = Decimal(row["our_tax"])
    official_tax = Decimal(row["official_tax"])

    difference = abs(our_tax - official_tax)
    row["difference"] = str(difference)
    row["status"] = "MATCH" if difference == 0 else "MISMATCH"

    completed += 1
    matched += difference == 0
    differences.append(difference)

with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\nOFFICIAL VALIDATION SUMMARY")
print("---------------------------")
print("Completed comparisons:", completed)
print("Matched:", matched)
print("Mismatched:", completed - matched)

if completed:
    print("Accuracy:", round(matched / completed * 100, 2), "%")
    print("Average absolute tax difference:",
          sum(differences) / completed)
else:
    print("No official results entered yet.")
    