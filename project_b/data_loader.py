"""
Data loading and fallback generation pipeline for NYC 311 Service Requests.
Supports loading from local CSV, attempting remote fetch from NYC Open Data,
and a reproducible synthetic fallback dataset clearly labelled as synthetic.
"""

import os
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd
import requests

from project_b.config import DomainConfig


# Schema fields aligned with NYC Open Data 311 Service Requests view definition
NYC_311_COLUMNS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "location_type",
    "incident_zip",
    "incident_address",
    "street_name",
    "city",
    "status",
    "resolution_description",
    "borough",
    "latitude",
    "longitude",
]


def generate_synthetic_nyc311_dataset(
    n_rows: int = 1000,
    random_seed: int = 42,
    domain: Optional[DomainConfig] = None
) -> pd.DataFrame:
    """
    Generate a reproducible synthetic NYC 311 dataset for development, testing,
    and fallback when live Open Data endpoints are inaccessible.

    NOTE ON PROVENANCE:
    This dataset is SYNTHETIC test data generated from standard NYC 311 schema fields.
    It is NOT an empirical extract of 2023 records.
    """
    if domain is None:
        domain = DomainConfig()

    rng = random.Random(random_seed)

    agencies_and_complaints = [
        ("NYPD", "New York City Police Department", "Illegal Parking", "Blocked Hydrant", "Street/Sidewalk"),
        ("NYPD", "New York City Police Department", "Noise - Residential", "Loud Music/Party", "Residential Building/House"),
        ("NYPD", "New York City Police Department", "Blocked Driveway", "No Access", "Street/Sidewalk"),
        ("HPD", "Department of Housing Preservation and Development", "HEAT/HOT WATER", "ENTIRE BUILDING", "RESIDENTIAL BUILDING"),
        ("HPD", "Department of Housing Preservation and Development", "PLUMBING", "WATER LEAK", "RESIDENTIAL BUILDING"),
        ("DOT", "Department of Transportation", "Street Condition", "Pothole", "Highway"),
        ("DOT", "Department of Transportation", "Street Light Condition", "Street Light Out", "Sidewalk"),
        ("DSNY", "Department of Sanitation", "Dirty Condition", "Trash/Garbage", "Sidewalk"),
        ("DEP", "Department of Environmental Protection", "Water System", "Hydrant Running Full", "Street"),
        ("DOB", "Department of Buildings", "Building/Use", "Illegal Conversion", "Building"),
        ("DPR", "Department of Parks and Recreation", "Damaged Tree", "Branch Cracked", "Park"),
    ]

    borough_zip_map = {
        "MANHATTAN": ("NEW YORK", [10001, 10002, 10011, 10019, 10025, 10028]),
        "BROOKLYN": ("BROOKLYN", [11201, 11211, 11215, 11222, 11226, 11238]),
        "QUEENS": ("QUEENS", [11101, 11354, 11375, 11432, 11691]),
        "BRONX": ("BRONX", [10451, 10458, 10467, 10468, 10471]),
        "STATEN ISLAND": ("STATEN ISLAND", [10301, 10304, 10306, 10312, 10314]),
    }

    borough_centers = {
        "MANHATTAN": (40.7831, -73.9712),
        "BROOKLYN": (40.6782, -73.9442),
        "QUEENS": (40.7282, -73.7949),
        "BRONX": (40.8448, -73.8648),
        "STATEN ISLAND": (40.5795, -74.1502),
    }

    base_date = datetime(2023, 1, 1, 0, 0, 0)
    records = []

    for i in range(n_rows):
        # 8-digit unique key typical of NYC 311
        unique_key = 50000000 + i

        agency, agency_name, complaint, desc, loc_type = rng.choice(agencies_and_complaints)
        borough = rng.choice(list(borough_zip_map.keys()))
        city, zips = borough_zip_map[borough]
        incident_zip = str(rng.choice(zips))

        # Created date spread over 2023
        created_offset = timedelta(
            days=rng.randint(0, 360),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
            seconds=rng.randint(0, 59)
        )
        created_dt = base_date + created_offset

        # 85% closed, 15% open/in-progress
        is_closed = rng.random() < 0.85
        if is_closed:
            status = "Closed"
            # Typical resolution between 2 hours and 120 hours
            duration_hours = max(0.5, rng.expovariate(1.0 / 24.0))
            closed_dt = created_dt + timedelta(hours=duration_hours)
            closed_str = closed_dt.strftime("%Y-%m-%d %H:%M:%S")
            res_desc = f"The {agency} responded to the complaint and resolved the condition."
        else:
            status = rng.choice(["Open", "In Progress", "Pending"])
            closed_str = None
            duration_hours = None
            res_desc = f"The {agency} has received the service request and investigation is underway."

        lat_c, lon_c = borough_centers[borough]
        # Jitter coordinates slightly within borough (~0.03 deg)
        lat = round(lat_c + rng.gauss(0, 0.015), 6)
        lon = round(lon_c + rng.gauss(0, 0.015), 6)

        street_num = rng.randint(10, 999)
        street_names = ["BROADWAY", "5 AVENUE", "BEDFORD AVENUE", "MAIN STREET", "ATLANTIC AVENUE", "GRAND CONCOURSE"]
        street = rng.choice(street_names)
        address = f"{street_num} {street}"

        records.append({
            "unique_key": str(unique_key),
            "created_date": created_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "closed_date": closed_str,
            "agency": agency,
            "agency_name": agency_name,
            "complaint_type": complaint,
            "descriptor": desc,
            "location_type": loc_type,
            "incident_zip": incident_zip,
            "incident_address": address,
            "street_name": street,
            "city": city,
            "status": status,
            "resolution_description": res_desc,
            "borough": borough,
            "latitude": lat,
            "longitude": lon,
            "resolution_time_hours": duration_hours,
        })

    df = pd.DataFrame(records)
    # Explicitly stamp provenance metadata
    df.attrs["data_source"] = "SYNTHETIC_FALLBACK"
    df.attrs["is_synthetic"] = True
    df.attrs["description"] = "Synthetic test dataset generated from NYC 311 schema fields."
    return df


def load_dataset(
    file_path: Optional[str] = None,
    sample_size: Optional[int] = None,
    random_seed: int = 42,
    domain: Optional[DomainConfig] = None
) -> Tuple[pd.DataFrame, str]:
    """
    Load dataset from a local CSV file if it exists, or fall back to reproducible synthetic data.

    Returns:
        (df, provenance_string)
    """
    if file_path and os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, low_memory=False)
            provenance = f"LOCAL_CSV ({file_path})"
            df.attrs["data_source"] = provenance
            df.attrs["is_synthetic"] = False
            # Ensure unique_key is string
            if "unique_key" in df.columns:
                df["unique_key"] = df["unique_key"].astype(str)
            if sample_size and sample_size < len(df):
                df = df.sample(n=sample_size, random_state=random_seed).reset_index(drop=True)
            return df, provenance
        except Exception as err:
            print(f"[WARN] Failed to read {file_path}: {err}. Falling back to synthetic generator.")

    # Fallback to synthetic generator
    n = sample_size if sample_size else 1000
    df = generate_synthetic_nyc311_dataset(n_rows=n, random_seed=random_seed, domain=domain)
    provenance = "SYNTHETIC_FALLBACK (Generated from NYC 311 schema)"
    return df, provenance
