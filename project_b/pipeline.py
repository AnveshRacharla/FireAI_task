"""
Hybrid Data Quality Pipeline for NYC 311 Service Requests.
Orchestrates rule-based, statistical, machine-learning, and LLM detectors.
Performs intelligent alert deduplication, confidence fusion,
detector explanation preservation, and severity-based prioritization.
"""

from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from project_b.schemas import DetectionAlert, Severity, SEVERITY_WEIGHTS
from project_b.config import PipelineConfig
from project_b.detectors.base import BaseDetector
from project_b.detectors.rule_based import RuleBasedDetector
from project_b.detectors.statistical import StatisticalDetector
from project_b.detectors.ml_based import MLBasedDetector
from project_b.detectors.llm_based import LLMBasedDetector


class HybridDataQualityPipeline:
    """
    Production hybrid pipeline uniting rules, statistics, ML, and LLMs.
    Configurable, modular, deduplicated, and prioritized.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        reference_df: Optional[pd.DataFrame] = None
    ):
        self.config = config or PipelineConfig()
        self.detectors: Dict[str, BaseDetector] = {}

        # Initialize active detectors based on configuration
        if self.config.enable_rules:
            self.detectors["rule_based"] = RuleBasedDetector(domain_config=self.config.domain)

        if self.config.enable_statistical:
            self.detectors["statistical"] = StatisticalDetector(
                reference_df=reference_df,
                config=self.config.statistical
            )

        if self.config.enable_ml:
            self.detectors["machine_learning"] = MLBasedDetector(
                reference_df=reference_df,
                config=self.config.ml
            )

        if self.config.enable_llm:
            self.detectors["llm_based"] = LLMBasedDetector(config=self.config.llm)

    def fit(self, reference_df: pd.DataFrame) -> "HybridDataQualityPipeline":
        """Calibrate statistical and ML models on baseline reference data."""
        if "statistical" in self.detectors:
            stat_det = self.detectors["statistical"]
            if hasattr(stat_det, "fit"):
                stat_det.fit(reference_df)

        if "machine_learning" in self.detectors:
            ml_det = self.detectors["machine_learning"]
            if hasattr(ml_det, "fit"):
                ml_det.fit(reference_df)

        return self

    def run(self, df: pd.DataFrame) -> List[DetectionAlert]:
        """
        Execute all active detectors, merge and deduplicate overlapping alerts,
        preserve individual detector rationales, and prioritize by urgency.

        Returns:
            List[DetectionAlert]: Sorted by priority score descending.
        """
        if df.empty:
            return []

        all_raw_alerts: List[DetectionAlert] = []

        # 1. Run each enabled detector
        for name, detector in self.detectors.items():
            try:
                detector_alerts = detector.detect(df)
                all_raw_alerts.extend(detector_alerts)
            except Exception as err:
                print(f"[ERROR] Detector '{name}' encountered an error: {err}")

        # 2. If deduplication disabled, simply sort and return
        if not self.config.deduplicate_alerts:
            all_raw_alerts.sort(key=lambda a: a.priority_score, reverse=True)
            return all_raw_alerts

        # 3. Deduplicate and fuse overlapping alerts
        fused_alerts = self._deduplicate_alerts(all_raw_alerts)

        # 4. Filter by confidence threshold and sort by priority score
        final_alerts = [
            alert for alert in fused_alerts
            if alert.confidence >= self.config.min_confidence_threshold
        ]
        final_alerts.sort(key=lambda a: a.priority_score, reverse=True)

        return final_alerts

    def _deduplicate_alerts(self, alerts: List[DetectionAlert]) -> List[DetectionAlert]:
        """
        Group alerts by (row_id, primary_category) and fuse them.
        Combines confidence scores, escalates severity on consensus,
        and aggregates detector explanations.
        """
        groups: Dict[Tuple[str, str], List[DetectionAlert]] = {}

        # Issue category normalization mapping to cluster similar findings
        issue_clusters = {
            "missing_values": "missing",
            "duplicate_records": "duplicate",
            "invalid_dates": "temporal",
            "inconsistent_timestamps": "temporal",
            "invalid_categorical": "categorical",
            "invalid_coordinates": "spatial",
            "impossible_numeric": "numeric",
            "outliers": "numeric",
            "invalid_ids": "identity",
            "malformed_text": "text",
            "cross_column_inconsistency": "relational",
            "distribution_shift": "drift",
        }

        for alert in alerts:
            cluster = issue_clusters.get(alert.detected_issue, alert.detected_issue)
            # Use tuple of row_id and cluster as fusion key
            key = (str(alert.row_id), cluster)
            groups.setdefault(key, []).append(alert)

        fused_results: List[DetectionAlert] = []

        for (row_id, cluster), group in groups.items():
            if len(group) == 1:
                single = group[0]
                single.contributing_detectors = [single.detector_name]
                fused_results.append(single)
                continue

            # Multi-detector consensus fusion
            contributing = list(dict.fromkeys(a.detector_name for a in group))
            primary_issue = group[0].detected_issue

            # Combine confidence via probabilistic union: 1 - product(1 - c_i)
            prod_complement = 1.0
            for a in group:
                prod_complement *= max(0.01, (1.0 - a.confidence))
            fused_confidence = round(min(0.999, 1.0 - prod_complement), 4)

            # Determine fused severity: escalate if multiple detectors agree
            severities = [a.severity.upper() for a in group]
            if Severity.CRITICAL.value in severities:
                fused_severity = Severity.CRITICAL.value
            elif severities.count(Severity.HIGH.value) >= 2 or (Severity.HIGH.value in severities and len(group) >= 2):
                fused_severity = Severity.CRITICAL.value
            elif Severity.HIGH.value in severities:
                fused_severity = Severity.HIGH.value
            elif Severity.MEDIUM.value in severities:
                fused_severity = Severity.MEDIUM.value
            else:
                fused_severity = Severity.LOW.value

            # Combine columns
            all_cols = []
            for a in group:
                if a.column and a.column not in all_cols:
                    all_cols.append(a.column)
            fused_col = ",".join(all_cols) if all_cols else group[0].column

            # Preserve and concatenate distinct detector-level explanations
            explanations = [f"[{a.detector_name}] {a.explanation}" for a in group]
            fused_explanation = f"Consensus alert ({', '.join(contributing)}): " + " | ".join(explanations)

            fused_alert = DetectionAlert(
                row_id=row_id,
                column=fused_col,
                detected_issue=primary_issue,
                detector_name="hybrid",
                severity=fused_severity,
                confidence=fused_confidence,
                explanation=fused_explanation,
                contributing_detectors=contributing,
                metadata={"fused_count": len(group)}
            )
            fused_results.append(fused_alert)

        return fused_results
