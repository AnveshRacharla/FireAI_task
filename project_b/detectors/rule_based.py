"""
Rule-based data quality detector for NYC 311 Service Requests.
Validates structural schema, regex patterns, domain invariants,
and cross-column logic deterministically.
"""

import re
from datetime import datetime
from typing import List, Optional, Set, Dict, Any
import pandas as pd

from project_b.schemas import DetectionAlert, Severity
from project_b.config import DomainConfig
from project_b.detectors.base import BaseDetector


class RuleBasedDetector(BaseDetector):
    """
    Deterministic rule-based detector implementing schema checks,
    domain value constraints, regex validations, and cross-column rules.
    """

    def __init__(self, domain_config: Optional[DomainConfig] = None):
        super().__init__(name="rule_based")
        self.domain = domain_config or DomainConfig()

    def detect(self, df: pd.DataFrame) -> List[DetectionAlert]:
        alerts: List[DetectionAlert] = []

        if df.empty:
            return alerts

        # 1. Duplicate unique_key / duplicate rows check
        if "unique_key" in df.columns:
            duplicated_mask = df.duplicated(subset=["unique_key"], keep=False)
            dup_indices = df[duplicated_mask].index
            for idx in dup_indices:
                row_key = str(df.at[idx, "unique_key"])
                alerts.append(DetectionAlert(
                    row_id=row_key,
                    column="unique_key",
                    detected_issue="duplicate_records",
                    detector_name=self.name,
                    severity=Severity.HIGH.value,
                    confidence=1.0,
                    explanation=f"Duplicate unique_key '{row_key}' detected across multiple records."
                ))

        for idx, row in df.iterrows():
            row_id = str(row.get("unique_key", f"row_{idx}"))

            # 2. Invalid IDs check (unique_key format)
            raw_key = str(row.get("unique_key", "")).strip()
            if not raw_key or not raw_key.isdigit() or len(raw_key) != 8:
                alerts.append(DetectionAlert(
                    row_id=row_id,
                    column="unique_key",
                    detected_issue="invalid_ids",
                    detector_name=self.name,
                    severity=Severity.CRITICAL.value,
                    confidence=0.99,
                    explanation=f"Identifier '{raw_key}' is invalid. Expected 8-digit numeric unique_key."
                ))

            # 3. Missing values check on critical fields
            critical_cols = ["complaint_type", "created_date", "incident_zip", "borough"]
            for col in critical_cols:
                if col in df.columns:
                    val = row.get(col)
                    if pd.isna(val) or val is None or str(val).strip() == "" or str(val).lower() == "nan":
                        alerts.append(DetectionAlert(
                            row_id=row_id,
                            column=col,
                            detected_issue="missing_values",
                            detector_name=self.name,
                            severity=Severity.HIGH.value,
                            confidence=1.0,
                            explanation=f"Critical field '{col}' is missing or null."
                        ))

            # 4. Invalid dates check & Inconsistent timestamps check
            created_dt: Optional[datetime] = None
            closed_dt: Optional[datetime] = None

            for date_col in ["created_date", "closed_date"]:
                if date_col in df.columns:
                    raw_dt = row.get(date_col)
                    if pd.notna(raw_dt) and raw_dt is not None and str(raw_dt).strip() != "":
                        try:
                            parsed = pd.to_datetime(raw_dt)
                            if date_col == "created_date":
                                created_dt = parsed
                            elif date_col == "closed_date":
                                closed_dt = parsed

                            # Future date check
                            if parsed.year > 2026:
                                alerts.append(DetectionAlert(
                                    row_id=row_id,
                                    column=date_col,
                                    detected_issue="invalid_dates",
                                    detector_name=self.name,
                                    severity=Severity.HIGH.value,
                                    confidence=0.95,
                                    explanation=f"Field '{date_col}' has impossible future year {parsed.year} ('{raw_dt}')."
                                ))
                        except Exception:
                            alerts.append(DetectionAlert(
                                row_id=row_id,
                                column=date_col,
                                detected_issue="invalid_dates",
                                detector_name=self.name,
                                severity=Severity.HIGH.value,
                                confidence=1.0,
                                explanation=f"Field '{date_col}' contains unparseable date string '{raw_dt}'."
                            ))

            # Timestamp chronological consistency
            if created_dt is not None and closed_dt is not None:
                if closed_dt < created_dt:
                    alerts.append(DetectionAlert(
                        row_id=row_id,
                        column="created_date,closed_date",
                        detected_issue="inconsistent_timestamps",
                        detector_name=self.name,
                        severity=Severity.CRITICAL.value,
                        confidence=1.0,
                        explanation=f"Closed date ({closed_dt}) is chronologically earlier than created date ({created_dt})."
                    ))

            # 5. Invalid categorical values (borough, agency)
            if "borough" in df.columns:
                borough_val = str(row.get("borough", "")).strip().upper()
                if borough_val and borough_val not in self.domain.valid_boroughs:
                    alerts.append(DetectionAlert(
                        row_id=row_id,
                        column="borough",
                        detected_issue="invalid_categorical",
                        detector_name=self.name,
                        severity=Severity.HIGH.value,
                        confidence=0.98,
                        explanation=f"Borough value '{borough_val}' is not recognized in NYC domain."
                    ))

            if "agency" in df.columns:
                agency_val = str(row.get("agency", "")).strip().upper()
                if agency_val and agency_val not in self.domain.valid_agencies:
                    alerts.append(DetectionAlert(
                        row_id=row_id,
                        column="agency",
                        detected_issue="invalid_categorical",
                        detector_name=self.name,
                        severity=Severity.HIGH.value,
                        confidence=0.95,
                        explanation=f"Agency '{agency_val}' is not recognized in NYC municipal agencies list."
                    ))

            # 6. Invalid geographic coordinates (out of bounding box or (0,0))
            if "latitude" in df.columns and "longitude" in df.columns:
                raw_lat = row.get("latitude")
                raw_lon = row.get("longitude")
                if pd.notna(raw_lat) and pd.notna(raw_lon):
                    try:
                        lat = float(raw_lat)
                        lon = float(raw_lon)
                        if abs(lat) < 1e-4 and abs(lon) < 1e-4:
                            alerts.append(DetectionAlert(
                                row_id=row_id,
                                column="latitude,longitude",
                                detected_issue="invalid_coordinates",
                                detector_name=self.name,
                                severity=Severity.HIGH.value,
                                confidence=0.99,
                                explanation="Coordinates (0.0, 0.0) fall on 'Null Island' outside NYC."
                            ))
                        elif not (self.domain.min_latitude <= lat <= self.domain.max_latitude and
                                  self.domain.min_longitude <= lon <= self.domain.max_longitude):
                            alerts.append(DetectionAlert(
                                row_id=row_id,
                                column="latitude,longitude",
                                detected_issue="invalid_coordinates",
                                detector_name=self.name,
                                severity=Severity.HIGH.value,
                                confidence=0.95,
                                explanation=f"Coordinates ({lat}, {lon}) fall outside NYC geographic bounding box."
                            ))
                    except (ValueError, TypeError):
                        alerts.append(DetectionAlert(
                            row_id=row_id,
                            column="latitude,longitude",
                            detected_issue="invalid_coordinates",
                            detector_name=self.name,
                            severity=Severity.HIGH.value,
                            confidence=0.99,
                            explanation=f"Non-numeric coordinate values: lat='{raw_lat}', lon='{raw_lon}'."
                        ))

            # 7. Negative or impossible numeric values
            if "resolution_time_hours" in df.columns:
                raw_res = row.get("resolution_time_hours")
                if pd.notna(raw_res):
                    try:
                        res_val = float(raw_res)
                        if res_val < 0:
                            alerts.append(DetectionAlert(
                                row_id=row_id,
                                column="resolution_time_hours",
                                detected_issue="impossible_numeric",
                                detector_name=self.name,
                                severity=Severity.CRITICAL.value,
                                confidence=1.0,
                                explanation=f"Negative resolution time '{res_val}' is physically impossible."
                            ))
                    except (ValueError, TypeError):
                        pass

            if "incident_zip" in df.columns:
                raw_zip = str(row.get("incident_zip", "")).strip()
                if raw_zip.startswith("-"):
                    alerts.append(DetectionAlert(
                        row_id=row_id,
                        column="incident_zip",
                        detected_issue="impossible_numeric",
                        detector_name=self.name,
                        severity=Severity.HIGH.value,
                        confidence=0.99,
                        explanation=f"Negative postal zip code '{raw_zip}' is impossible."
                    ))

            # 8. Malformed text (HTML tags, unprintable chars, unicode corruption)
            for text_col in ["descriptor", "resolution_description"]:
                if text_col in df.columns:
                    raw_text = row.get(text_col)
                    if pd.notna(raw_text) and raw_text is not None:
                        text_str = str(raw_text)
                        if "\ufffd" in text_str or any(ord(c) < 32 and c not in "\n\r\t" for c in text_str):
                            alerts.append(DetectionAlert(
                                row_id=row_id,
                                column=text_col,
                                detected_issue="malformed_text",
                                detector_name=self.name,
                                severity=Severity.MEDIUM.value,
                                confidence=0.95,
                                explanation=f"Field '{text_col}' contains unprintable or corrupted encoding characters."
                            ))
                        elif "<script" in text_str.lower() or "alert(" in text_str.lower():
                            alerts.append(DetectionAlert(
                                row_id=row_id,
                                column=text_col,
                                detected_issue="malformed_text",
                                detector_name=self.name,
                                severity=Severity.HIGH.value,
                                confidence=0.98,
                                explanation=f"Field '{text_col}' contains suspicious code or script injection tags."
                            ))

            # 9. Cross-column inconsistencies
            # A. Agency vs Complaint type check
            if "agency" in df.columns and "complaint_type" in df.columns:
                agency_val = str(row.get("agency", "")).strip()
                c_type = str(row.get("complaint_type", "")).strip()
                # Known strict contradiction: NYPD handling HEAT/HOT WATER
                if agency_val == "NYPD" and "HEAT/HOT WATER" in c_type.upper():
                    alerts.append(DetectionAlert(
                        row_id=row_id,
                        column="agency,complaint_type",
                        detected_issue="cross_column_inconsistency",
                        detector_name=self.name,
                        severity=Severity.HIGH.value,
                        confidence=0.92,
                        explanation="Agency 'NYPD' has no jurisdiction over 'HEAT/HOT WATER' (HPD jurisdiction)."
                    ))

            # B. Borough vs ZIP prefix check
            if "borough" in df.columns and "incident_zip" in df.columns:
                b_val = str(row.get("borough", "")).strip().upper()
                z_val = str(row.get("incident_zip", "")).strip()
                if b_val in self.domain.borough_zip_prefixes and len(z_val) >= 3 and z_val[:3].isdigit():
                    expected_prefixes = self.domain.borough_zip_prefixes[b_val]
                    if not any(z_val.startswith(p) for p in expected_prefixes):
                        alerts.append(DetectionAlert(
                            row_id=row_id,
                            column="borough,incident_zip",
                            detected_issue="cross_column_inconsistency",
                            detector_name=self.name,
                            severity=Severity.MEDIUM.value,
                            confidence=0.88,
                            explanation=f"ZIP '{z_val}' does not match typical prefixes {expected_prefixes} for borough '{b_val}'."
                        ))

            # C. Status vs Closed Date check
            status_val = str(row.get("status", "")).strip()
            closed_val = row.get("closed_date")
            if status_val == "Closed" and (pd.isna(closed_val) or str(closed_val).strip() == ""):
                alerts.append(DetectionAlert(
                    row_id=row_id,
                    column="status,closed_date",
                    detected_issue="cross_column_inconsistency",
                    detector_name=self.name,
                    severity=Severity.MEDIUM.value,
                    confidence=0.90,
                    explanation="Record has status 'Closed' but missing 'closed_date'."
                ))

        return alerts
