
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

OUTPUT_PATH = Path("project_a/data/compiled_tax_rules.json")


def validate_rules(rules):
    """Check that Gemini returned the expected structure and slab counts."""

    expected_years = {
        "2024-25": (6, 4, 4, 3),
        "2025-26": (7, 4, 4, 3)
    }

    if set(rules.keys()) != set(expected_years.keys()):
        raise ValueError("Unexpected financial years in compiled rules")

    for year, counts in expected_years.items():
        year_rules = rules[year]

        new_count, below_60, senior, super_senior = counts

        if len(year_rules["new_regime"]) != new_count:
            raise ValueError(f"Invalid new regime slabs for {year}")

        old = year_rules["old_regime"]

        if len(old["below_60"]) != below_60:
            raise ValueError(f"Invalid below-60 slabs for {year}")

        if len(old["senior_60_to_79"]) != senior:
            raise ValueError(f"Invalid senior slabs for {year}")

        if len(old["super_senior_80_plus"]) != super_senior:
            raise ValueError(f"Invalid super-senior slabs for {year}")

        # Validate slab fields and continuity.
        for slab_list in [
            year_rules["new_regime"],
            old["below_60"],
            old["senior_60_to_79"],
            old["super_senior_80_plus"]
        ]:
            for slab in slab_list:
                if set(slab.keys()) != {"lower", "upper", "rate"}:
                    raise ValueError("Invalid slab fields")

                if slab["lower"] < 0 or not 0 <= slab["rate"] <= 1:
                    raise ValueError("Invalid slab value")

            for current, following in zip(slab_list, slab_list[1:]):
                if current["upper"] != following["lower"]:
                    raise ValueError("Slab boundaries are not continuous")

            if slab_list[-1]["upper"] is not None:
                raise ValueError("Last slab must have no upper limit")


def compile_tax_rules():
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    client = genai.Client(api_key=API_KEY)

    prompt = """
Convert the following supplied Indian income-tax slab specifications
into structured JSON.

IMPORTANT:
- Do not change any numerical values.
- Do not add or remove slabs.
- Do not calculate or infer tax rates.
- Preserve all age categories.
- Return exactly the JSON structure shown below.
- Return valid JSON only, without Markdown.

{
  "2024-25": {
    "new_regime": [
      {"lower": 0, "upper": 300000, "rate": 0},
      {"lower": 300000, "upper": 600000, "rate": 0.05},
      {"lower": 600000, "upper": 900000, "rate": 0.10},
      {"lower": 900000, "upper": 1200000, "rate": 0.15},
      {"lower": 1200000, "upper": 1500000, "rate": 0.20},
      {"lower": 1500000, "upper": null, "rate": 0.30}
    ],
    "old_regime": {
      "below_60": [
        {"lower": 0, "upper": 250000, "rate": 0},
        {"lower": 250000, "upper": 500000, "rate": 0.05},
        {"lower": 500000, "upper": 1000000, "rate": 0.20},
        {"lower": 1000000, "upper": null, "rate": 0.30}
      ],
      "senior_60_to_79": [
        {"lower": 0, "upper": 300000, "rate": 0},
        {"lower": 300000, "upper": 500000, "rate": 0.05},
        {"lower": 500000, "upper": 1000000, "rate": 0.20},
        {"lower": 1000000, "upper": null, "rate": 0.30}
      ],
      "super_senior_80_plus": [
        {"lower": 0, "upper": 500000, "rate": 0},
        {"lower": 500000, "upper": 1000000, "rate": 0.20},
        {"lower": 1000000, "upper": null, "rate": 0.30}
      ]
    }
  },
  "2025-26": {
    "new_regime": [
      {"lower": 0, "upper": 400000, "rate": 0},
      {"lower": 400000, "upper": 800000, "rate": 0.05},
      {"lower": 800000, "upper": 1200000, "rate": 0.10},
      {"lower": 1200000, "upper": 1600000, "rate": 0.15},
      {"lower": 1600000, "upper": 2000000, "rate": 0.20},
      {"lower": 2000000, "upper": 2400000, "rate": 0.25},
      {"lower": 2400000, "upper": null, "rate": 0.30}
    ],
    "old_regime": {
      "below_60": [
        {"lower": 0, "upper": 250000, "rate": 0},
        {"lower": 250000, "upper": 500000, "rate": 0.05},
        {"lower": 500000, "upper": 1000000, "rate": 0.20},
        {"lower": 1000000, "upper": null, "rate": 0.30}
      ],
      "senior_60_to_79": [
        {"lower": 0, "upper": 300000, "rate": 0},
        {"lower": 300000, "upper": 500000, "rate": 0.05},
        {"lower": 500000, "upper": 1000000, "rate": 0.20},
        {"lower": 1000000, "upper": null, "rate": 0.30}
      ],
      "super_senior_80_plus": [
        {"lower": 0, "upper": 500000, "rate": 0},
        {"lower": 500000, "upper": 1000000, "rate": 0.20},
        {"lower": 1000000, "upper": null, "rate": 0.30}
      ]
    }
  }
}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )

    rules = json.loads(response.text)

    # Validate before replacing the existing file.
    validate_rules(rules)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(rules, file, indent=4)

    print("Tax rules compiled successfully!")
    print("Financial years:", ", ".join(rules.keys()))
    print("Saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    compile_tax_rules()
