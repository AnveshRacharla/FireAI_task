"""
Tests for rule-based data quality detector.
"""

import pytest
import pandas as pd
from project_b.detectors.rule_based import RuleBasedDetector
from project_b.config import DomainConfig


@pytest.fixture
def detector():
    return RuleBasedDetector(domain_config=DomainConfig())


def test_rule_detects_invalid_id(detector):
    df = pd.DataFrame([{
        "unique_key": "INVALID_ID_99",
        "created_date": "2023-01-01 10:00:00",
        "complaint_type": "Illegal Parking",
        "borough": "MANHATTAN"
    }])
    alerts = detector.detect(df)
    issues = [a.detected_issue for a in alerts]
    assert "invalid_ids" in issues


def test_rule_detects_missing_critical(detector):
    df = pd.DataFrame([{
        "unique_key": "50000001",
        "created_date": "2023-01-01 10:00:00",
        "complaint_type": None,
        "borough": "BROOKLYN"
    }])
    alerts = detector.detect(df)
    issues = [a.detected_issue for a in alerts]
    assert "missing_values" in issues


def test_rule_detects_invalid_categorical(detector):
    df = pd.DataFrame([{
        "unique_key": "50000002",
        "created_date": "2023-01-01 10:00:00",
        "complaint_type": "Illegal Parking",
        "borough": "ATLANTIS"
    }])
    alerts = detector.detect(df)
    issues = [a.detected_issue for a in alerts]
    assert "invalid_categorical" in issues


def test_rule_detects_inconsistent_timestamps(detector):
    df = pd.DataFrame([{
        "unique_key": "50000003",
        "created_date": "2023-01-05 10:00:00",
        "closed_date": "2023-01-02 10:00:00",
        "complaint_type": "Noise",
        "borough": "QUEENS"
    }])
    alerts = detector.detect(df)
    issues = [a.detected_issue for a in alerts]
    assert "inconsistent_timestamps" in issues


def test_rule_detects_invalid_coordinates(detector):
    df = pd.DataFrame([{
        "unique_key": "50000004",
        "latitude": 0.0,
        "longitude": 0.0,
        "created_date": "2023-01-01 10:00:00",
        "complaint_type": "Pothole",
        "borough": "BRONX"
    }])
    alerts = detector.detect(df)
    issues = [a.detected_issue for a in alerts]
    assert "invalid_coordinates" in issues


def test_rule_detects_cross_column_mismatch(detector):
    df = pd.DataFrame([{
        "unique_key": "50000005",
        "agency": "NYPD",
        "complaint_type": "HEAT/HOT WATER",
        "created_date": "2023-01-01 10:00:00",
        "borough": "MANHATTAN"
    }])
    alerts = detector.detect(df)
    issues = [a.detected_issue for a in alerts]
    assert "cross_column_inconsistency" in issues
