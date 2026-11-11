"""
Evaluation metrics engine for the NYC 311 Data Quality Engine.
Computes Precision, Recall, F1, False Positive Rate, Latency, Throughput,
and Estimated Cost per 1M rows, strictly distinguishing measured from estimated figures.
"""

from typing import List, Dict, Any, Optional, Set
import pandas as pd

from project_b.schemas import DetectionAlert, GroundTruthRecord, EvaluationMetrics
from project_b.detectors.base import BaseDetector


class Evaluator:
    """
    Evaluates detector performance against known ground-truth corruptions.
    Calculates statistical classification metrics and operational benchmarks.
    """

    # Estimated cloud compute / API cost baselines per million rows (USD)
    ESTIMATED_COST_PER_MILLION: Dict[str, float] = {
        "rule_based": 0.002,         # Negligible CPU compute
        "statistical": 0.005,        # Vectorized numpy compute
        "machine_learning": 0.080,   # Isolation Forest inference compute
        "llm_based": 18.500,         # Selective batch LLM API token inference
        "hybrid": 1.250,             # Hybrid tiered routing (Rules/ML on 100%, LLM on 5% triage)
        "hybrid_pipeline": 1.250,    # Alias for normalized detector name
    }

    @classmethod
    def evaluate_detector(
        cls,
        detector_name: str,
        alerts: List[DetectionAlert],
        ground_truth: List[GroundTruthRecord],
        total_rows: int,
        latency_seconds: float,
        detector_instance: Optional[BaseDetector] = None
    ) -> EvaluationMetrics:
        """
        Evaluate a single detector's alerts against ground truth.
        """
        # Ground truth corrupted row IDs
        gt_row_ids: Set[str] = {
            str(gt.row_id) for gt in ground_truth if gt.row_id != "__dataset__"
        }
        has_gt_drift = any(gt.row_id == "__dataset__" for gt in ground_truth)

        # Flagged row IDs
        flagged_row_ids: Set[str] = {
            str(a.row_id) for a in alerts if a.row_id != "__dataset__"
        }
        has_flagged_drift = any(a.row_id == "__dataset__" for a in alerts)

        # Classification counts
        tp_rows = flagged_row_ids.intersection(gt_row_ids)
        fp_rows = flagged_row_ids.difference(gt_row_ids)
        fn_rows = gt_row_ids.difference(flagged_row_ids)

        tp = len(tp_rows)
        fp = len(fp_rows)
        fn = len(fn_rows)

        # Dataset-level drift evaluation
        if has_gt_drift:
            if has_flagged_drift:
                tp += 1
            else:
                fn += 1
        elif has_flagged_drift:
            fp += 1

        # Clean rows in dataset
        clean_rows_count = max(0, total_rows - len(gt_row_ids))
        tn = max(0, clean_rows_count - fp)

        # Precision, Recall, F1, FPR
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        # Latency & throughput
        safe_latency = max(latency_seconds, 1e-6)
        latency_per_row_ms = (safe_latency * 1000.0) / max(1, total_rows)
        throughput = total_rows / safe_latency

        # Cost lookup with normalized key
        normalized_key = detector_name.lower().replace("-", "_").replace(" ", "_")
        est_cost = cls.ESTIMATED_COST_PER_MILLION.get(normalized_key, 0.01)

        # Check for live API stats if available
        api_calls = 0
        api_tokens = 0
        if detector_instance and hasattr(detector_instance, "get_stats"):
            stats = detector_instance.get_stats()
            api_calls = stats.get("actual_api_calls", 0)
            api_tokens = stats.get("actual_input_tokens", 0) + stats.get("actual_output_tokens", 0)

        return EvaluationMetrics(
            detector_name=detector_name,
            total_rows_evaluated=total_rows,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            false_positive_rate=round(fpr, 4),
            detection_latency_seconds=round(safe_latency, 4),
            latency_per_row_ms=round(latency_per_row_ms, 4),
            throughput_rows_per_second=round(throughput, 1),
            estimated_cost_per_million_rows_usd=est_cost,
            actual_api_calls_made=api_calls,
            actual_api_tokens_used=api_tokens,
            is_cost_estimated=True,
        )

    @staticmethod
    def format_comparison_table(metrics_list: List[EvaluationMetrics]) -> str:
        """
        Format a Markdown comparison table across all evaluated approaches.
        Explicitly distinguishes measured metrics from estimates.
        """
        header = (
            "| Detector Approach | Precision | Recall | F1-Score | FPR | "
            "Latency (s) | Per-Row (ms) | Throughput (rows/s) | Est. Cost / 1M Rows (USD) |\n"
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
        )
        lines = [header]

        for m in metrics_list:
            cost_label = f"${m.estimated_cost_per_million_rows_usd:.3f}*"
            line = (
                f"| **{m.detector_name}** | {m.precision:.2%} | {m.recall:.2%} | {m.f1_score:.4f} | "
                f"{m.false_positive_rate:.2%} | {m.detection_latency_seconds:.3f}s | "
                f"{m.latency_per_row_ms:.3f}ms | {m.throughput_rows_per_second:,.1f} | {cost_label} |"
            )
            lines.append(line)

        lines.append("\n*Note: Metrics for Precision, Recall, F1, FPR, Latency, and Throughput are **empirically measured** from the test run. Cost per 1M rows is an **estimate** based on cloud CPU runtime and current Gemini 3.5 API token pricing.*")
        return "\n".join(lines)
