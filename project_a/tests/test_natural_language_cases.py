
from project_a.data.natural_language_cases import NATURAL_LANGUAGE_CASES


def test_natural_language_dataset_has_50_cases():
    assert len(NATURAL_LANGUAGE_CASES) == 50
    assert all(isinstance(case, str) for case in NATURAL_LANGUAGE_CASES)
    assert all(case.strip() for case in NATURAL_LANGUAGE_CASES)
