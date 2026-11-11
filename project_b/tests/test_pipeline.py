"""
Tests for Hybrid Data Quality Pipeline (deduplication, prioritization, explanation preservation).
"""

import pytest
import pandas as pd
from project_b.config import PipelineConfig, LLMConfig
from project_b.pipeline import HybridDataQualityPipeline
from project_b.schemas import Severity


@pytest.fixture
def sample_corrupt_df():
    return pd.DataFrame([
        {
            "unique_key": "50000001",
            "created_date": "2023-01-05 10:00:00",
            "closed_date": "2023-01-02 10:00:00",  # Inconsistent timestamps
            "resolution_time_hours": -72.0,        # Impossible negative numeric
            "agency": "NYPD",
            "complaint_type": "Illegal Parking",
            "descriptor": "Blocked driveway",
            "borough": "MANHATTAN",
            "incident_zip": "10001",
            "latitude": 40.75,
            "longitude": -73.98
        },
        {
            "unique_key": "50000002",
            "created_date": "2023-01-01 10:00:00",
            "closed_date": "2023-01-02 10:00:00",
            "resolution_time_hours": 24.0,
            "agency": "NYPD",
            "complaint_type": "Illegal Parking",
            "descriptor": "<script>alert(1)</script>",  # Malformed text
            "borough": "BROOKLYN",
            "incident_zip": "11201",
            "latitude": 40.69,
            "longitude": -73.99
        }
    ])


def test_hybrid_pipeline_deduplication(sample_corrupt_df):
    """Verify overlapping detector alerts are fused and explanations preserved."""
    cfg = PipelineConfig(
        enable_rules=True,
        enable_statistical=True,
        enable_ml=False,
        llm=LLMConfig(offline_mode=True),
        deduplicate_alerts=True
    )
    pipeline = HybridDataQualityPipeline(config=cfg)
    alerts = pipeline.run(sample_corrupt_df)

    assert len(alerts) > 0
    # Alerts must be sorted by priority score descending
    scores = [a.priority_score for a in alerts]
    assert scores == sorted(scores, reverse=True)

    # Check detector-level explanation preservation
    fused_with_consensus = [a for a in alerts if len(a.contributing_detectors) > 1]
    if fused_with_consensus:
        sample_fused = fused_with_consensus[0]
        assert "Consensus alert" in sample_fused.explanation
        assert all(det in sample_fused.explanation for det in sample_fused.contributing_detectors)


def test_pipeline_modular_toggles(sample_corrupt_df):
    """Verify detectors can be toggled on and off cleanly."""
    # Only rule-based enabled
    cfg_rules_only = PipelineConfig(
        enable_rules=True,
        enable_statistical=False,
        enable_ml=False,
        enable_llm=False
    )
    pipeline = HybridDataQualityPipeline(config=cfg_rules_only)
    assert set(pipeline.detectors.keys()) == {"rule_based"}
    alerts = pipeline.run(sample_corrupt_df)
    assert all(a.detector_name == "rule_based" or "rule_based" in a.contributing_detectors for a in alerts)
