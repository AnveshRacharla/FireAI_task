"""
Tests for evaluation metrics computation.
"""

import pytest
from project_b.schemas import DetectionAlert, GroundTruthRecord, Severity
from project_b.evaluation import Evaluator


def test_evaluator_metrics_math():
    """Verify precision, recall, f1, fpr calculations."""
    ground_truth = [
        GroundTruthRecord("row_1", "created_date", "invalid_dates", "2023-01-01", "bad_date"),
        GroundTruthRecord("row_2", "borough", "invalid_categorical", "MANHATTAN", "ATLANTIS"),
        GroundTruthRecord("row_3", "unique_key", "invalid_ids", "50000003", "KEY#3"),
    ]

    alerts = [
        # True Positives: row_1, row_2
        DetectionAlert("row_1", "created_date", "invalid_dates", "rule_based", Severity.HIGH.value, 1.0, "bad date"),
        DetectionAlert("row_2", "borough", "invalid_categorical", "rule_based", Severity.HIGH.value, 1.0, "bad borough"),
        # False Positive: row_4 (clean row falsely flagged)
        DetectionAlert("row_4", "complaint_type", "missing_values", "rule_based", Severity.MEDIUM.value, 0.7, "spurious alert"),
    ]

    total_rows = 10  # 3 corrupted rows (row_1, row_2, row_3), 7 clean rows (row_4 to row_10)

    metrics = Evaluator.evaluate_detector(
        detector_name="TestDetector",
        alerts=alerts,
        ground_truth=ground_truth,
        total_rows=total_rows,
        latency_seconds=0.1
    )

    # TP = 2 (row_1, row_2)
    # FP = 1 (row_4)
    # FN = 1 (row_3)
    # TN = 6 (7 clean rows minus 1 FP)
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.true_negatives == 6

    # Precision = 2 / 3 = 0.6667
    assert metrics.precision == pytest.approx(0.6667, abs=1e-3)
    # Recall = 2 / 3 = 0.6667
    assert metrics.recall == pytest.approx(0.6667, abs=1e-3)
    # F1 = 0.6667
    assert metrics.f1_score == pytest.approx(0.6667, abs=1e-3)
    # FPR = 1 / (1 + 6) = 0.1429
    assert metrics.false_positive_rate == pytest.approx(0.1429, abs=1e-3)

    assert metrics.throughput_rows_per_second == pytest.approx(100.0, abs=1e-1)
    assert metrics.is_cost_estimated is True
