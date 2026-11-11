"""
Tests for machine learning Isolation Forest detector.
"""

import pytest
import pandas as pd
from project_b.data_loader import generate_synthetic_nyc311_dataset
from project_b.detectors.ml_based import MLBasedDetector


@pytest.fixture
def ref_df():
    return generate_synthetic_nyc311_dataset(n_rows=150, random_seed=42)


def test_ml_detector_training(ref_df):
    detector = MLBasedDetector(reference_df=ref_df)
    assert detector.is_fitted is True
    assert detector.name == "machine_learning"


def test_ml_detects_spatial_anomalies(ref_df):
    detector = MLBasedDetector(reference_df=ref_df)

    # Invert or inject coordinate far outside normal space
    outlier_df = pd.DataFrame([
        {
            "unique_key": "50000888",
            "latitude": 0.0,
            "longitude": 0.0,
            "resolution_time_hours": 24.0,
            "borough": "MANHATTAN",
            "agency": "NYPD"
        },
        {
            "unique_key": "50000889",
            "latitude": 51.5074,  # London latitude
            "longitude": -0.1278,
            "resolution_time_hours": 24.0,
            "borough": "QUEENS",
            "agency": "DOT"
        }
    ])
    alerts = detector.detect(outlier_df)
    assert len(alerts) > 0
    flagged_ids = [a.row_id for a in alerts]
    assert "50000888" in flagged_ids or "50000889" in flagged_ids
    assert all(a.detector_name == "machine_learning" for a in alerts)
    assert all("isolation_forest_score" in a.metadata for a in alerts)
