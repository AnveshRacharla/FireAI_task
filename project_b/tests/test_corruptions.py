"""
Tests for corruption injection engine covering all 12 corruption types.
"""

import pytest
import pandas as pd
from project_b.data_loader import generate_synthetic_nyc311_dataset
from project_b.corruptions import CorruptionInjector


@pytest.fixture
def clean_df():
    return generate_synthetic_nyc311_dataset(n_rows=100, random_seed=42)


def test_all_12_corruptions_injected(clean_df):
    """Verify all 12 corruption types are injected and tracked in ground truth."""
    injector = CorruptionInjector(random_seed=42)
    corrupted_df, ground_truth = injector.inject_all(clean_df, injection_rate_per_type=0.03)

    assert len(corrupted_df) >= len(clean_df)
    assert len(ground_truth) > 0

    found_types = {gt.corruption_type for gt in ground_truth}
    for expected_type in CorruptionInjector.CORRUPTION_TYPES:
        assert expected_type in found_types, f"Corruption type '{expected_type}' was not injected."


def test_deterministic_injection(clean_df):
    """Verify that using the same random seed yields identical corruptions."""
    injector1 = CorruptionInjector(random_seed=99)
    df1, gt1 = injector1.inject_all(clean_df)

    injector2 = CorruptionInjector(random_seed=99)
    df2, gt2 = injector2.inject_all(clean_df)

    assert len(gt1) == len(gt2)
    for r1, r2 in zip(gt1, gt2):
        assert r1.corruption_type == r2.corruption_type
        assert r1.row_id == r2.row_id
        assert r1.corrupted_value == r2.corrupted_value


def test_ground_truth_integrity(clean_df):
    """Verify ground truth records contain non-empty metadata and valid row_ids."""
    injector = CorruptionInjector(random_seed=123)
    _, ground_truth = injector.inject_all(clean_df)

    for record in ground_truth:
        assert record.row_id is not None
        assert record.corruption_type in CorruptionInjector.CORRUPTION_TYPES
        assert "reason" in record.metadata
