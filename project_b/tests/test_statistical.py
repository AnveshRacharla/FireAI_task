"""
Tests for statistical anomaly detector and distribution drift.
"""

import pytest
import pandas as pd
from project_b.data_loader import generate_synthetic_nyc311_dataset
from project_b.detectors.statistical import StatisticalDetector


@pytest.fixture
def ref_df():
    return generate_synthetic_nyc311_dataset(n_rows=200, random_seed=42)


def test_statistical_calibration(ref_df):
    detector = StatisticalDetector(reference_df=ref_df)
    assert detector.is_fitted is True
    assert "resolution_time_hours" in detector.numeric_stats
    assert "borough" in detector.category_distributions


def test_statistical_detects_numeric_outlier(ref_df):
    detector = StatisticalDetector(reference_df=ref_df)
    test_df = pd.DataFrame([{
        "unique_key": "50000099",
        "resolution_time_hours": 50000.0,  # ~5.7 years
        "borough": "MANHATTAN"
    }])
    alerts = detector.detect(test_df)
    assert any(a.detected_issue == "outliers" and a.column == "resolution_time_hours" for a in alerts)


def test_statistical_detects_rare_category(ref_df):
    detector = StatisticalDetector(reference_df=ref_df)
    test_df = pd.DataFrame([{
        "unique_key": "50000100",
        "resolution_time_hours": 24.0,
        "borough": "NEVERLAND"
    }])
    alerts = detector.detect(test_df)
    assert any(a.detected_issue == "invalid_categorical" and a.column == "borough" for a in alerts)


def test_statistical_detects_distribution_shift(ref_df):
    detector = StatisticalDetector(reference_df=ref_df)
    # Create batch heavily skewed to STATEN ISLAND (98%)
    shifted_data = []
    for i in range(50):
        shifted_data.append({
            "unique_key": str(60000000 + i),
            "borough": "STATEN ISLAND",
            "resolution_time_hours": 20.0
        })
    shifted_df = pd.DataFrame(shifted_data)
    alerts = detector.detect(shifted_df)
    assert any(a.detected_issue == "distribution_shift" and a.row_id == "__dataset__" for a in alerts)
