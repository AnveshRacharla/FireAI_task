"""
Machine Learning data quality detector using scikit-learn IsolationForest.
Detects multivariate and spatial-temporal anomalies across numerical
and encoded categorical dimensions.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from project_b.schemas import DetectionAlert, Severity
from project_b.config import MLConfig
from project_b.detectors.base import BaseDetector


class MLBasedDetector(BaseDetector):
    """
    Multivariate anomaly detector powered by scikit-learn's IsolationForest.
    Extracts numerical coordinates, duration metrics, and categorical frequency encodings
    to detect complex multi-dimensional outliers without relying on hardcoded heuristics.
    """

    def __init__(
        self,
        reference_df: Optional[pd.DataFrame] = None,
        config: Optional[MLConfig] = None
    ):
        super().__init__(name="machine_learning")
        self.config = config or MLConfig()
        self.model = IsolationForest(
            n_estimators=self.config.n_estimators,
            contamination=self.config.contamination,
            random_state=self.config.random_state,
            n_jobs=-1
        )
        self.is_fitted = False
        self.feature_means: Dict[str, float] = {}
        self.cat_freq_maps: Dict[str, Dict[str, float]] = {}

        if reference_df is not None and len(reference_df) >= 20:
            self.fit(reference_df)

    def _extract_features(self, df: pd.DataFrame, is_training: bool = False) -> np.ndarray:
        """
        Transform raw NYC 311 DataFrame into a clean numeric matrix for Isolation Forest.
        """
        features_list = []

        # 1. Geographic coordinates
        for col in ["latitude", "longitude"]:
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce")
                if is_training:
                    mean_val = float(s.dropna().median()) if not s.dropna().empty else (40.7128 if col == "latitude" else -74.0060)
                    self.feature_means[col] = mean_val
                else:
                    mean_val = self.feature_means.get(col, 40.7128 if col == "latitude" else -74.0060)
                filled = s.fillna(mean_val).values
                features_list.append(filled)

        # 2. Resolution duration (log-transformed to stabilize skew)
        if "resolution_time_hours" in df.columns:
            s = pd.to_numeric(df["resolution_time_hours"], errors="coerce")
            # Replace negatives or nulls with median during training
            s_clean = s.apply(lambda x: np.nan if (pd.isna(x) or x < 0) else x)
            if is_training:
                dur_med = float(s_clean.dropna().median()) if not s_clean.dropna().empty else 24.0
                self.feature_means["resolution_time_hours"] = dur_med
            else:
                dur_med = self.feature_means.get("resolution_time_hours", 24.0)

            # Cap values for numerical stability prior to log transform
            clipped = np.clip(s_clean.fillna(dur_med).values, 0.01, 100000.0)
            log_dur = np.log1p(clipped)
            features_list.append(log_dur)

        # 3. Categorical frequency encodings (borough, agency)
        for cat_col in ["borough", "agency"]:
            if cat_col in df.columns:
                series = df[cat_col].astype(str).str.strip().str.upper()
                if is_training:
                    freq_map = series.value_counts(normalize=True).to_dict()
                    self.cat_freq_maps[cat_col] = freq_map
                else:
                    freq_map = self.cat_freq_maps.get(cat_col, {})

                encoded = series.map(lambda x: freq_map.get(x, 0.0)).values
                features_list.append(encoded)

        if not features_list:
            # Fallback dummy feature if no expected columns present
            return np.zeros((len(df), 1))

        return np.column_stack(features_list)

    def fit(self, reference_df: pd.DataFrame) -> "MLBasedDetector":
        """Fit Isolation Forest on baseline reference data."""
        X = self._extract_features(reference_df, is_training=True)
        if len(X) >= 10:
            self.model.fit(X)
            self.is_fitted = True
        return self

    def detect(self, df: pd.DataFrame) -> List[DetectionAlert]:
        alerts: List[DetectionAlert] = []

        if df.empty:
            return alerts

        # Auto-fit if not already fitted
        if not self.is_fitted:
            self.fit(df)

        if not self.is_fitted:
            return alerts

        X = self._extract_features(df, is_training=False)

        # Isolation forest scores: lower score = more anomalous
        scores = self.model.score_samples(X)
        predictions = self.model.predict(X)  # -1 indicates anomaly

        # Derive dynamic score threshold from contamination
        score_cutoff = np.percentile(scores, self.config.score_threshold_percentile)

        for idx, (score, pred) in enumerate(zip(scores, predictions)):
            if pred == -1 or score <= score_cutoff:
                row_id = str(df.at[idx, "unique_key"]) if "unique_key" in df.columns else f"row_{idx}"

                # Calculate confidence normalized from anomaly score
                # score_samples typically ranges between -0.8 and 0.2
                # Lower score implies higher anomaly confidence
                conf = min(0.98, max(0.45, round(float(1.0 - (score - (-0.8)) / 1.0), 3)))

                # Determine which feature likely contributed most to anomaly
                lat = df.at[idx, "latitude"] if "latitude" in df.columns else None
                lon = df.at[idx, "longitude"] if "longitude" in df.columns else None
                dur = df.at[idx, "resolution_time_hours"] if "resolution_time_hours" in df.columns else None

                explanation_notes = []
                issue_type = "outliers"
                flagged_col = "multivariate_features"

                if lat is not None and lon is not None:
                    try:
                        f_lat, f_lon = float(lat), float(lon)
                        if abs(f_lat) < 1.0 or abs(f_lat - 40.7) > 1.0:
                            explanation_notes.append(f"spatial coordinates ({f_lat}, {f_lon})")
                            issue_type = "invalid_coordinates"
                            flagged_col = "latitude,longitude"
                    except (ValueError, TypeError):
                        pass

                if dur is not None:
                    try:
                        f_dur = float(dur)
                        if f_dur > 5000.0 or f_dur < 0:
                            explanation_notes.append(f"extreme resolution time ({f_dur:.1f}h)")
                            issue_type = "outliers"
                            flagged_col = "resolution_time_hours"
                    except (ValueError, TypeError):
                        pass

                if not explanation_notes:
                    explanation_notes.append("unusual joint feature combination")

                explanation = (
                    f"Isolation Forest flagged multivariate anomaly (anomaly score={score:.3f}). "
                    f"Deviant characteristics: {', '.join(explanation_notes)}."
                )

                severity = Severity.HIGH.value if score < -0.6 else Severity.MEDIUM.value

                alerts.append(DetectionAlert(
                    row_id=row_id,
                    column=flagged_col,
                    detected_issue=issue_type,
                    detector_name=self.name,
                    severity=severity,
                    confidence=conf,
                    explanation=explanation,
                    metadata={"isolation_forest_score": round(float(score), 4)}
                ))

        return alerts
