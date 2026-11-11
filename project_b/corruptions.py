"""
Synthetic corruption injection engine for NYC 311 data.
Implements 12 distinct corruption types with deterministic injection
and exact ground-truth tracking for rigorous evaluation.
"""

import random
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd

from project_b.schemas import GroundTruthRecord


class CorruptionInjector:
    """
    Injects 12 realistic data corruption types into a dataset
    while maintaining exact ground truth annotations.
    """

    CORRUPTION_TYPES = [
        "missing_values",
        "duplicate_records",
        "invalid_dates",
        "invalid_categorical",
        "invalid_coordinates",
        "impossible_numeric",
        "outliers",
        "inconsistent_timestamps",
        "invalid_ids",
        "malformed_text",
        "cross_column_inconsistency",
        "distribution_shift",
    ]

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self.rng = random.Random(random_seed)
        self.np_rng = np.random.RandomState(random_seed)

    def inject_all(
        self,
        df: pd.DataFrame,
        injection_rate_per_type: float = 0.02
    ) -> Tuple[pd.DataFrame, List[GroundTruthRecord]]:
        """
        Inject all 12 corruption types into copies of disjoint or targeted rows
        to create an evaluation dataset with known ground truth.

        Returns:
            (corrupted_df, ground_truth_records)
        """
        corrupted_df = df.copy().reset_index(drop=True)
        ground_truth: List[GroundTruthRecord] = []
        n_rows = len(corrupted_df)

        if n_rows < 50:
            raise ValueError(f"Dataset must have at least 50 rows for reliable corruption injection (got {n_rows}).")

        # Calculate number of rows to perturb per corruption type
        k = max(2, int(n_rows * injection_rate_per_type))

        # Partition available rows to ensure each row gets a clear single corruption
        available_indices = list(range(n_rows))
        self.rng.shuffle(available_indices)

        def take_indices(count: int) -> List[int]:
            nonlocal available_indices
            if len(available_indices) < count:
                # Reuse if exhausted
                available_indices = list(range(n_rows))
                self.rng.shuffle(available_indices)
            chosen = available_indices[:count]
            available_indices = available_indices[count:]
            return chosen

        # 1. Missing Values (critical columns nullified)
        idx_missing = take_indices(k)
        for idx in idx_missing:
            col = self.rng.choice(["complaint_type", "created_date", "incident_zip", "borough"])
            orig_val = corrupted_df.at[idx, col]
            corrupted_df.at[idx, col] = None
            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column=col,
                corruption_type="missing_values",
                original_value=orig_val,
                corrupted_value=None,
                metadata={"reason": f"Nullified critical field {col}"}
            ))

        # 2. Duplicate Records (exact duplicate appended)
        idx_dup = take_indices(k)
        dup_rows = []
        for idx in idx_dup:
            row_copy = corrupted_df.iloc[idx].copy()
            orig_key = str(row_copy["unique_key"])
            dup_rows.append(row_copy)
            ground_truth.append(GroundTruthRecord(
                row_id=orig_key,
                column=None,
                corruption_type="duplicate_records",
                original_value=orig_key,
                corrupted_value=orig_key,
                metadata={"reason": "Exact duplicated record inserted"}
            ))
        if dup_rows:
            dup_df = pd.DataFrame(dup_rows)
            corrupted_df = pd.concat([corrupted_df, dup_df], ignore_index=True)

        # 3. Invalid Dates (unparseable or impossible dates)
        idx_dates = take_indices(k)
        invalid_date_values = ["99/99/2023 25:61:99", "2023-02-31 12:00:00", "not-a-valid-date", "2099-12-31 23:59:59"]
        for idx in idx_dates:
            target_col = self.rng.choice(["created_date", "closed_date"])
            orig_val = corrupted_df.at[idx, target_col]
            bad_date = self.rng.choice(invalid_date_values)
            corrupted_df.at[idx, target_col] = bad_date
            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column=target_col,
                corruption_type="invalid_dates",
                original_value=orig_val,
                corrupted_value=bad_date,
                metadata={"reason": "Injected unparseable or future date"}
            ))

        # 4. Invalid Categorical Values (illegal borough or non-existent agency)
        idx_cat = take_indices(k)
        for idx in idx_cat:
            if self.rng.random() < 0.5:
                col = "borough"
                bad_val = self.rng.choice(["ATLANTIS", "LONDON", "PARIS", "NEW_JERSEY_SHORE", "GOTHAM"])
            else:
                col = "agency"
                bad_val = self.rng.choice(["NASA", "PENTAGON", "INTERPOL", "UNKNOWN_AGY"])
            orig_val = corrupted_df.at[idx, col]
            corrupted_df.at[idx, col] = bad_val
            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column=col,
                corruption_type="invalid_categorical",
                original_value=orig_val,
                corrupted_value=bad_val,
                metadata={"reason": f"Injected non-existent domain category into {col}"}
            ))

        # 5. Invalid Geographic Coordinates (outside NYC, 0,0, or swapped lat/lon)
        idx_geo = take_indices(k)
        for idx in idx_geo:
            orig_lat = corrupted_df.at[idx, "latitude"]
            orig_lon = corrupted_df.at[idx, "longitude"]
            geo_choice = self.rng.choice(["null_island", "out_of_bounds", "swapped"])
            if geo_choice == "null_island":
                new_lat, new_lon = 0.0, 0.0
            elif geo_choice == "swapped":
                new_lat, new_lon = orig_lon, orig_lat  # Swapped coordinates
            else:
                new_lat, new_lon = 51.5074, -0.1278  # London, UK coords
            corrupted_df.at[idx, "latitude"] = new_lat
            corrupted_df.at[idx, "longitude"] = new_lon
            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column="latitude,longitude",
                corruption_type="invalid_coordinates",
                original_value=f"({orig_lat}, {orig_lon})",
                corrupted_value=f"({new_lat}, {new_lon})",
                metadata={"reason": f"Invalid geographic coordinates ({geo_choice})"}
            ))

        # 6. Negative or Impossible Numeric Values (negative resolution time, negative zip, negative ID)
        idx_num = take_indices(k)
        for idx in idx_num:
            num_choice = self.rng.choice(["negative_resolution", "negative_zip"])
            if num_choice == "negative_resolution":
                orig_val = corrupted_df.at[idx, "resolution_time_hours"]
                bad_val = -120.5
                corrupted_df.at[idx, "resolution_time_hours"] = bad_val
                target_col = "resolution_time_hours"
            else:
                orig_val = corrupted_df.at[idx, "incident_zip"]
                bad_val = "-10001"
                corrupted_df.at[idx, "incident_zip"] = bad_val
                target_col = "incident_zip"

            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column=target_col,
                corruption_type="impossible_numeric",
                original_value=orig_val,
                corrupted_value=bad_val,
                metadata={"reason": "Injected negative/impossible numeric value"}
            ))

        # 7. Outliers (extreme numeric values, e.g. 10 years to fix a pothole or 99999 hours)
        idx_outliers = take_indices(k)
        for idx in idx_outliers:
            orig_val = corrupted_df.at[idx, "resolution_time_hours"]
            extreme_val = round(self.rng.uniform(15000.0, 80000.0), 2)  # 2 to 9 years
            corrupted_df.at[idx, "resolution_time_hours"] = extreme_val
            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column="resolution_time_hours",
                corruption_type="outliers",
                original_value=orig_val,
                corrupted_value=extreme_val,
                metadata={"reason": "Extreme statistical outlier (> 15,000 hours)"}
            ))

        # 8. Inconsistent Timestamps (closed_date occurs BEFORE created_date)
        idx_ts = take_indices(k)
        for idx in idx_ts:
            c_date = corrupted_df.at[idx, "created_date"]
            # closed_date set to 2 days prior to created_date
            corrupted_df.at[idx, "closed_date"] = "2023-01-01 01:00:00"
            corrupted_df.at[idx, "created_date"] = "2023-01-03 14:00:00"
            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column="created_date,closed_date",
                corruption_type="inconsistent_timestamps",
                original_value=c_date,
                corrupted_value="closed_date < created_date",
                metadata={"reason": "Closed date is chronologically earlier than created date"}
            ))

        # 9. Invalid IDs (malformed unique_key: non-numeric, corrupted prefix, wrong length)
        idx_ids = take_indices(k)
        for idx in idx_ids:
            orig_id = str(corrupted_df.at[idx, "unique_key"])
            bad_id = self.rng.choice([f"ERR_KEY_{orig_id}", "ABC-123", "999", "INVALID#ID!"])
            corrupted_df.at[idx, "unique_key"] = bad_id
            ground_truth.append(GroundTruthRecord(
                row_id=bad_id,
                column="unique_key",
                corruption_type="invalid_ids",
                original_value=orig_id,
                corrupted_value=bad_id,
                metadata={"reason": "Unique key does not conform to standardized identifier pattern"}
            ))

        # 10. Malformed Text (corrupted character encodings, HTML injection, gibberish)
        idx_text = take_indices(k)
        for idx in idx_text:
            orig_desc = corrupted_df.at[idx, "descriptor"]
            bad_text = self.rng.choice([
                "???\ufffd\ufffd\ufffd CORRUPTED_ENCODING \x00\x01\x02",
                "<script>alert('xss_injection')</script>",
                "asdfkjhqwpoieurytlaksjdhfgzxcvbnm!@#$%^&*()_+",
                "   "
            ])
            corrupted_df.at[idx, "descriptor"] = bad_text
            ground_truth.append(GroundTruthRecord(
                row_id=str(corrupted_df.at[idx, "unique_key"]),
                column="descriptor",
                corruption_type="malformed_text",
                original_value=orig_desc,
                corrupted_value=bad_text,
                metadata={"reason": "Injected corrupted encoding, script tags, or unprintable characters"}
            ))

        # 11. Cross-Column Inconsistencies (Agency-Complaint contradiction or Borough-Zip contradiction)
        idx_cross = take_indices(k)
        for idx in idx_cross:
            contradiction_type = self.rng.choice(["agency_complaint", "borough_zip"])
            if contradiction_type == "agency_complaint":
                # NYPD handling HEAT/HOT WATER (which is HPD jurisdiction)
                orig_agy = corrupted_df.at[idx, "agency"]
                orig_c = corrupted_df.at[idx, "complaint_type"]
                corrupted_df.at[idx, "agency"] = "NYPD"
                corrupted_df.at[idx, "complaint_type"] = "HEAT/HOT WATER"
                ground_truth.append(GroundTruthRecord(
                    row_id=str(corrupted_df.at[idx, "unique_key"]),
                    column="agency,complaint_type",
                    corruption_type="cross_column_inconsistency",
                    original_value=f"{orig_agy} | {orig_c}",
                    corrupted_value="NYPD | HEAT/HOT WATER",
                    metadata={"reason": "Cross-column contradiction: NYPD does not handle HEAT/HOT WATER"}
                ))
            else:
                # MANHATTAN borough assigned a BROOKLYN zip code (11201)
                orig_b = corrupted_df.at[idx, "borough"]
                orig_z = corrupted_df.at[idx, "incident_zip"]
                corrupted_df.at[idx, "borough"] = "MANHATTAN"
                corrupted_df.at[idx, "incident_zip"] = "11201"
                ground_truth.append(GroundTruthRecord(
                    row_id=str(corrupted_df.at[idx, "unique_key"]),
                    column="borough,incident_zip",
                    corruption_type="cross_column_inconsistency",
                    original_value=f"{orig_b} | {orig_z}",
                    corrupted_value="MANHATTAN | 11201",
                    metadata={"reason": "Cross-column contradiction: Zip 11201 belongs to Brooklyn, not Manhattan"}
                ))

        # 12. Unexpected Distribution Shift (Batch/Dataset level drift)
        # Shift a sub-block of rows heavily towards one single borough (e.g. STATEN ISLAND 95%)
        # and record a dataset-level ground truth entry
        shift_size = max(5, int(n_rows * 0.15))
        shift_indices = take_indices(shift_size)
        orig_boroughs = [corrupted_df.at[i, "borough"] for i in shift_indices]
        for i in shift_indices:
            corrupted_df.at[i, "borough"] = "STATEN ISLAND"

        ground_truth.append(GroundTruthRecord(
            row_id="__dataset__",
            column="borough",
            corruption_type="distribution_shift",
            original_value=f"Diverse boroughs ({len(set(orig_boroughs))} unique)",
            corrupted_value="Heavy skew: 95%+ Staten Island concentrated in batch",
            metadata={
                "reason": "Sudden population shift in categorical distribution",
                "affected_indices_count": len(shift_indices)
            }
        ))

        return corrupted_df, ground_truth
