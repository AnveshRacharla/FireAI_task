"""
Tests for NYC 311 data loader and synthetic fallback generator.
"""

import os
import tempfile
import pandas as pd
import pytest

from project_b.data_loader import load_dataset, generate_synthetic_nyc311_dataset, NYC_311_COLUMNS


def test_generate_synthetic_dataset_structure():
    """Verify synthetic generator creates valid schema and provenance."""
    df = generate_synthetic_nyc311_dataset(n_rows=50, random_seed=42)
    assert len(df) == 50
    assert df.attrs.get("is_synthetic") is True
    assert "SYNTHETIC" in df.attrs.get("data_source", "")

    # Check key columns
    expected_cols = ["unique_key", "created_date", "agency", "complaint_type", "borough", "latitude", "longitude"]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col}"

    # Check unique_key format
    assert all(df["unique_key"].str.isdigit())
    assert all(df["unique_key"].str.len() == 8)


def test_load_dataset_from_csv():
    """Verify loading from an actual CSV file."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
        tmp.write("unique_key,created_date,agency,complaint_type,borough\n")
        tmp.write("50000001,2023-01-01 10:00:00,NYPD,Illegal Parking,MANHATTAN\n")
        tmp.write("50000002,2023-01-01 11:00:00,HPD,HEAT/HOT WATER,BRONX\n")
        tmp_path = tmp.name

    try:
        df, prov = load_dataset(file_path=tmp_path, sample_size=10, random_seed=42)
        assert len(df) == 2
        assert "LOCAL_CSV" in prov
        assert df.attrs.get("is_synthetic") is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_load_dataset_fallback():
    """Verify fallback to synthetic generator when file does not exist."""
    df, prov = load_dataset(file_path="non_existent_file_xyz.csv", sample_size=30, random_seed=42)
    assert len(df) == 30
    assert "SYNTHETIC_FALLBACK" in prov
    assert df.attrs.get("is_synthetic") is True
