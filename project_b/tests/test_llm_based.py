"""
Tests for LLM-based data quality detector.
"""

import pytest
import pandas as pd
from project_b.config import LLMConfig
from project_b.detectors.llm_based import LLMBasedDetector


def test_llm_offline_mode():
    """Verify offline mock detection runs deterministically without network."""
    cfg = LLMConfig(offline_mode=True)
    detector = LLMBasedDetector(config=cfg)

    test_df = pd.DataFrame([
        {
            "unique_key": "50000777",
            "agency": "NYPD",
            "complaint_type": "HEAT/HOT WATER",
            "descriptor": "Corrupted \ufffd\ufffd\ufffd text",
            "borough": "MANHATTAN"
        },
        {
            "unique_key": "50000778",
            "agency": "DOT",
            "complaint_type": "Street Condition",
            "descriptor": "<script>alert('xss')</script>",
            "borough": "BROOKLYN"
        }
    ])

    alerts = detector.detect(test_df)
    assert len(alerts) >= 2
    issues = [a.detected_issue for a in alerts]
    assert "malformed_text" in issues
    assert all(a.detector_name == "llm_based" for a in alerts)


@pytest.mark.integration
def test_llm_live_gemini():
    """Verify live Gemini API call when API key is available."""
    cfg = LLMConfig(offline_mode=False, max_rows_to_sample=2, batch_size=2)
    detector = LLMBasedDetector(config=cfg)

    if not detector.is_api_available():
        pytest.skip("GEMINI_API_KEY is not configured.")

    test_df = pd.DataFrame([
        {
            "unique_key": "50000999",
            "agency": "NYPD",
            "complaint_type": "HEAT/HOT WATER",
            "descriptor": "asdfkjh!@#$%^ gibberish text in descriptor",
            "borough": "MANHATTAN"
        }
    ])

    alerts = detector.detect(test_df)
    stats = detector.get_stats()
    assert stats["actual_api_calls"] >= 1
