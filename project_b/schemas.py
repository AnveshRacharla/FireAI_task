"""
Standard schemas for NYC 311 Data Quality Engine.
Defines standardized data quality alerts, ground truth records, and evaluation metrics.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class Severity(str, Enum):
    """Alert severity levels for prioritization."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


SEVERITY_WEIGHTS: Dict[str, float] = {
    Severity.CRITICAL.value: 1.0,
    Severity.HIGH.value: 0.75,
    Severity.MEDIUM.value: 0.50,
    Severity.LOW.value: 0.25,
    Severity.INFO.value: 0.10,
}


@dataclass
class DetectionAlert:
    """
    Standardized alert produced by all detection approaches.
    """
    row_id: Any                  # Row identifier (e.g., unique_key or integer index)
    column: Optional[str]        # Column name or comma-separated columns; '__dataset__' for dataset-level issues
    detected_issue: str          # Descriptive name of the detected issue / corruption type
    detector_name: str           # 'rule_based', 'statistical', 'machine_learning', 'llm_based', or 'hybrid'
    severity: str                # Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
    confidence: float            # Confidence score between 0.0 and 1.0
    explanation: str             # Clear, human-readable diagnostic explanation
    contributing_detectors: List[str] = field(default_factory=list)  # In hybrid alerts, lists all detectors that agreed
    metadata: Dict[str, Any] = field(default_factory=dict)          # Optional extra context (e.g., z-score, token count)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to a dictionary representation."""
        return asdict(self)

    @property
    def priority_score(self) -> float:
        """
        Calculate alert priority: severity weight multiplied by confidence.
        Higher priority indicates more urgent issues.
        """
        weight = SEVERITY_WEIGHTS.get(self.severity.upper(), 0.5)
        return round(weight * self.confidence, 4)


@dataclass
class GroundTruthRecord:
    """
    Ground truth annotation for injected synthetic corruptions.
    """
    row_id: Any
    column: Optional[str]
    corruption_type: str
    original_value: Any
    corrupted_value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationMetrics:
    """
    Evaluation metrics for a detector or hybrid pipeline against known ground truth.
    """
    detector_name: str
    total_rows_evaluated: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    detection_latency_seconds: float
    latency_per_row_ms: float
    throughput_rows_per_second: float
    estimated_cost_per_million_rows_usd: float
    actual_api_calls_made: int = 0
    actual_api_tokens_used: int = 0
    is_cost_estimated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
