
import json
from pathlib import Path

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.calculator import compare_regimes


def normalize(data):
    return json.loads(json.dumps(data, default=str, sort_keys=True))


def test_all_220_numerical_cases():
    path = Path("project_a/data/numerical_test_cases.json")

    with path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    assert len(cases) >= 200

    for case in cases:
        taxpayer = TaxpayerInput(**case["input"])

        actual = compare_regimes(taxpayer)
        expected = case["expected_output"]

        assert normalize(actual) == normalize(expected), (
            f"Mismatch in case {case['case_id']}"
        )
