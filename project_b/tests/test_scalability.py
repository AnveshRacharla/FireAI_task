"""
Tests for multi-tenant manager and micro-batch scalability components.
"""

import pytest
import pandas as pd
from project_b.scalability import MultiTenantManager, MicroBatchValidator
from project_b.config import PipelineConfig, LLMConfig
from project_b.pipeline import HybridDataQualityPipeline


def test_multi_tenant_isolation_and_quotas():
    manager = MultiTenantManager()
    cfg = PipelineConfig(enable_llm=False)

    ctx = manager.register_tenant("tenant_ny_parks", "NYC Parks Dept", config=cfg, max_daily_rows=100)
    assert ctx.tenant_id == "tenant_ny_parks"
    assert ctx.rows_processed_today == 0

    df_batch = pd.DataFrame([
        {
            "unique_key": f"500000{i:02d}",
            "created_date": "2023-01-01 10:00:00",
            "agency": "DPR",
            "complaint_type": "Damaged Tree",
            "borough": "QUEENS"
        }
        for i in range(10)
    ])

    alerts = manager.process_tenant_batch("tenant_ny_parks", df_batch)
    assert ctx.rows_processed_today == 10

    # Test quota enforcement
    oversized_df = pd.DataFrame([
        {"unique_key": f"500001{i:02d}", "created_date": "2023-01-01 10:00:00", "complaint_type": "Tree", "borough": "BRONX"}
        for i in range(100)
    ])
    with pytest.raises(PermissionError):
        manager.process_tenant_batch("tenant_ny_parks", oversized_df)


def test_micro_batch_validator():
    pipeline = HybridDataQualityPipeline(config=PipelineConfig(enable_llm=False))
    validator = MicroBatchValidator(pipeline=pipeline, batch_size=5)

    df = pd.DataFrame([
        {
            "unique_key": f"500000{i:02d}",
            "created_date": "2023-01-01 10:00:00",
            "agency": "NYPD",
            "complaint_type": "Noise",
            "borough": "MANHATTAN"
        }
        for i in range(12)
    ])

    # Should process 12 rows across 3 batches (5 + 5 + 2)
    alerts = validator.process_stream(df)
    assert isinstance(alerts, list)
