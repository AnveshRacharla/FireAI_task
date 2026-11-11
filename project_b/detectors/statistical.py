"""
Statistical data quality detector for NYC 311 Service Requests.
Calculates statistical thresholds (Z-score, IQR, rare-frequency, PSI drift)
calibrated from a reference dataset.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from project_b.schemas import DetectionAlert, Severity
from project_b.config import StatisticalConfig
from project_b.detectors.base import BaseDetector


class StatisticalDetector(BaseDetector):
    """
    Statistical anomaly detector calibrated against a reference baseline.
    Detects univariate numeric outliers, rare categorical deviations,
    and dataset-level distribution drift.
    """

    def __init__(
        self,
        reference_df: Optional[pd.DataFrame] = None,
        config: Optional[StatisticalConfig] = None
    ):
        super().__init__(name="statistical")
        self.config = config or StatisticalConfig()

        # Computed reference statistics
        self.numeric_stats: Dict[str, Dict[str, float]] = {}
        self.category_distributions: Dict[str, Dict[str, float]] = {}
        self.is_fitted = False

        if reference_df is not None and not reference_df.empty:
            self.fit(reference_df)

    def fit(self, reference_df: pd.DataFrame) -> "StatisticalDetector":
        """
        Calibrate baseline statistical profiles from a reference dataset.
        """
        # 1. Numeric columns (resolution_time_hours, latitude, longitude)
        numeric_cols = ["resolution_time_hours", "latitude", "longitude"]
        for col in numeric_cols:
            if col in reference_df.columns:
                series = pd.to_numeric(reference_df[col], errors="coerce").dropna()
                # Exclude extreme unphysical negatives when establishing reference baseline
                clean_series = series[series >= 0] if col == "resolution_time_hours" else series
                if len(clean_series) > 10:
                    q25 = float(clean_series.quantile(0.25))
                    q75 = float(clean_series.quantile(0.75))
                    iqr = q75 - q25
                    mean = float(clean_series.mean())
                    std = float(clean_series.std()) if clean_series.std() > 1e-6 else 1.0

                    self.numeric_stats[col] = {
                        "mean": mean,
                        "std": std,
                        "q25": q25,
                        "q75": q75,
                        "iqr": iqr,
                        "upper_bound_iqr": q75 + (self.config.iqr_multiplier * iqr),
                        "lower_bound_iqr": max(0.0, q25 - (self.config.iqr_multiplier * iqr)) if col == "resolution_time_hours" else q25 - (self.config.iqr_multiplier * iqr),
                    }

        # 2. Categorical columns distributions
        cat_cols = ["borough", "agency", "complaint_type"]
        for col in cat_cols:
            if col in reference_df.columns:
                series = reference_df[col].dropna().astype(str).str.strip().str.upper()
                counts = series.value_counts(normalize=True).to_dict()
                self.category_distributions[col] = counts

        self.is_fitted = True
        return self

    def detect(self, df: pd.DataFrame) -> List[DetectionAlert]:
        alerts: List[DetectionAlert] = []

        if df.empty:
            return alerts

        # Auto-fit on clean portion of dataset if not explicitly pre-fitted
        if not self.is_fitted:
            self.fit(df)

        # 1. Numeric Outlier Detection (Z-score + IQR)
        for col, stats in self.numeric_stats.items():
            if col not in df.columns:
                continue

            for idx, row in df.iterrows():
                row_id = str(row.get("unique_key", f"row_{idx}"))
                raw_val = row.get(col)

                if pd.isna(raw_val) or raw_val is None:
                    continue

                try:
                    val = float(raw_val)
                except (ValueError, TypeError):
                    continue

                # Skip negative values handled by rule-based impossible numerics
                if col == "resolution_time_hours" and val < 0:
                    continue

                z_score = abs(val - stats["mean"]) / stats["std"]
                is_iqr_outlier = val > stats["upper_bound_iqr"] or (val < stats["lower_bound_iqr"] and col != "resolution_time_hours")

                if z_score > self.config.z_score_threshold or is_iqr_outlier:
                    conf = min(0.99, max(0.50, round(1.0 - np.exp(-z_score / 3.0), 3)))
                    severity = Severity.HIGH.value if z_score > 5.0 else Severity.MEDIUM.value
                    alerts.append(DetectionAlert(
                        row_id=row_id,
                        column=col,
                        detected_issue="outliers",
                        detector_name=self.name,
                        severity=severity,
                        confidence=conf,
                        explanation=f"Statistical outlier in '{col}' (value={val:.2f}, mean={stats['mean']:.2f}, z-score={z_score:.2f}).",
                        metadata={"z_score": round(z_score, 2), "value": val}
                    ))

        # 2. Rare or Unseen Categorical Anomaly Detection
        for col, dist in self.category_distributions.items():
            if col not in df.columns:
                continue

            for idx, row in df.iterrows():
                row_id = str(row.get("unique_key", f"row_{idx}"))
                raw_val = row.get(col)

                if pd.isna(raw_val) or raw_val is None:
                    continue

                cat_key = str(raw_val).strip().upper()
                ref_freq = dist.get(cat_key, 0.0)

                # Flag if unseen in reference or significantly below frequency threshold
                if ref_freq < self.config.rare_category_frequency_threshold:
                    alerts.append(DetectionAlert(
                        row_id=row_id,
                        column=col,
                        detected_issue="invalid_categorical",
                        detector_name=self.name,
                        severity=Severity.HIGH.value if ref_freq == 0.0 else Severity.LOW.value,
                        confidence=0.92 if ref_freq == 0.0 else 0.65,
                        explanation=f"Rare or anomalous category '{raw_val}' in '{col}' (reference frequency={ref_freq:.4f}).",
                        metadata={"ref_frequency": ref_freq}
                    ))

        # 3. Distribution Shift / Drift Detection (Batch Level)
        for col, ref_dist in self.category_distributions.items():
            if col not in df.columns or len(df) < 20:
                continue

            current_series = df[col].dropna().astype(str).str.strip().str.upper()
            if current_series.empty:
                continue

            curr_dist = current_series.value_counts(normalize=True).to_dict()

            # Calculate Total Variation Distance (TVD) = 0.5 * sum(|P(x) - Q(x)|)
            all_keys = set(ref_dist.keys()).union(set(curr_dist.keys()))
            tvd = 0.5 * sum(abs(curr_dist.get(k, 0.0) - ref_dist.get(k, 0.0)) for k in all_keys)

            if tvd > self.config.distribution_shift_threshold:
                # Find the most heavily skewed category
                max_diff_cat = max(all_keys, key=lambda k: abs(curr_dist.get(k, 0.0) - ref_dist.get(k, 0.0)))
                c_freq = curr_dist.get(max_diff_cat, 0.0)
                r_freq = ref_dist.get(max_diff_cat, 0.0)

                alerts.append(DetectionAlert(
                    row_id="__dataset__",
                    column=col,
                    detected_issue="distribution_shift",
                    detector_name=self.name,
                    severity=Severity.HIGH.value,
                    confidence=min(0.99, round(tvd, 3)),
                    explanation=(
                        f"Significant distribution shift detected in '{col}' "
                        f"(Total Variation Distance={tvd:.3f} > threshold {self.config.distribution_shift_threshold}). "
                        f"Key driver: '{max_diff_cat}' shifted from {r_freq:.1%} to {c_freq:.1%}."
                    ),
                    metadata={"tvd": round(tvd, 4), "skewed_category": max_diff_cat}
                ))

        return alerts
