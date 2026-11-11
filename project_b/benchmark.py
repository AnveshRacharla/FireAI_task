"""
Benchmark and evaluation runner for the NYC 311 Data Quality Engine.
Runs all four detection methods and the hybrid pipeline on the exact same
corrupted dataset and ground truth, computing rigorous empirical metrics.
"""

import os
import json
import time
import argparse
from typing import Dict, Any, List
import pandas as pd

from project_b.config import PipelineConfig
from project_b.data_loader import load_dataset, generate_synthetic_nyc311_dataset
from project_b.corruptions import CorruptionInjector
from project_b.detectors.rule_based import RuleBasedDetector
from project_b.detectors.statistical import StatisticalDetector
from project_b.detectors.ml_based import MLBasedDetector
from project_b.detectors.llm_based import LLMBasedDetector
from project_b.pipeline import HybridDataQualityPipeline
from project_b.evaluation import Evaluator
from project_b.schemas import EvaluationMetrics


def run_benchmark(
    input_file: str = None,
    sample_size: int = 1000,
    random_seed: int = 42,
    output_dir: str = "project_b/results"
) -> Dict[str, Any]:
    """
    Execute full empirical evaluation across all 5 approaches.
    """
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 70)
    print("NYC 311 DATA QUALITY ENGINE - BENCHMARK & EVALUATION")
    print("=" * 70)

    # 1. Load Data
    print(f"\n[1/5] Loading NYC 311 dataset (sample_size={sample_size})...")
    df_raw, provenance = load_dataset(
        file_path=input_file,
        sample_size=sample_size + 400,  # extra rows for reference baseline
        random_seed=random_seed
    )
    print(f"      Provenance: {provenance}")
    print(f"      Total records loaded: {len(df_raw)}")

    # 2. Split reference data for training statistical & ML detectors
    ref_size = min(400, int(len(df_raw) * 0.3))
    reference_df = df_raw.iloc[:ref_size].copy().reset_index(drop=True)
    eval_clean_df = df_raw.iloc[ref_size : ref_size + sample_size].copy().reset_index(drop=True)
    print(f"      Reference baseline size: {len(reference_df)} rows")
    print(f"      Evaluation clean base size: {len(eval_clean_df)} rows")

    # 3. Inject 12 synthetic corruptions with ground truth
    print("\n[2/5] Injecting 12 deterministic corruption types...")
    injector = CorruptionInjector(random_seed=random_seed)
    corrupted_df, ground_truth = injector.inject_all(eval_clean_df, injection_rate_per_type=0.02)
    print(f"      Corrupted dataset size: {len(corrupted_df)} rows")
    print(f"      Total ground-truth corruption events: {len(ground_truth)}")

    # Summary of injected corruption counts
    counts = {}
    for gt in ground_truth:
        counts[gt.corruption_type] = counts.get(gt.corruption_type, 0) + 1
    for c_type, count in sorted(counts.items()):
        print(f"        - {c_type:<30}: {count} occurrences")

    # 4. Instantiate all detectors & pipeline
    print("\n[3/5] Initializing detectors & hybrid pipeline...")
    cfg = PipelineConfig()
    rule_detector = RuleBasedDetector(domain_config=cfg.domain)
    stat_detector = StatisticalDetector(reference_df=reference_df, config=cfg.statistical)
    ml_detector = MLBasedDetector(reference_df=reference_df, config=cfg.ml)
    llm_detector = LLMBasedDetector(config=cfg.llm)

    hybrid_pipeline = HybridDataQualityPipeline(config=cfg, reference_df=reference_df)

    eval_targets = [
        ("Rule-Based", rule_detector),
        ("Statistical", stat_detector),
        ("Machine Learning", ml_detector),
        ("LLM-Based", llm_detector),
    ]

    metrics_results: List[EvaluationMetrics] = []

    # 5. Execute each individual detector
    print("\n[4/5] Running evaluation across all approaches on the exact same dataset...")
    total_eval_rows = len(corrupted_df)

    for name, detector in eval_targets:
        print(f"      Evaluating {name:<20}...", end="", flush=True)
        t0 = time.perf_counter()
        alerts = detector.detect(corrupted_df)
        elapsed = time.perf_counter() - t0

        metrics = Evaluator.evaluate_detector(
            detector_name=name,
            alerts=alerts,
            ground_truth=ground_truth,
            total_rows=total_eval_rows,
            latency_seconds=elapsed,
            detector_instance=detector
        )
        metrics_results.append(metrics)
        print(f" Done ({elapsed:.3f}s | Alerts: {len(alerts)} | F1: {metrics.f1_score:.4f})")

    # 6. Execute Hybrid Pipeline
    print(f"      Evaluating {'Hybrid Pipeline':<20}...", end="", flush=True)
    t0 = time.perf_counter()
    hybrid_alerts = hybrid_pipeline.run(corrupted_df)
    elapsed_hybrid = time.perf_counter() - t0

    hybrid_metrics = Evaluator.evaluate_detector(
        detector_name="Hybrid Pipeline",
        alerts=hybrid_alerts,
        ground_truth=ground_truth,
        total_rows=total_eval_rows,
        latency_seconds=elapsed_hybrid
    )
    metrics_results.append(hybrid_metrics)
    print(f" Done ({elapsed_hybrid:.3f}s | Alerts: {len(hybrid_alerts)} | F1: {hybrid_metrics.f1_score:.4f})")

    # 7. Print Results Table
    print("\n" + "=" * 70)
    print("EMPIRICAL EVALUATION RESULTS")
    print("=" * 70)
    table_md = Evaluator.format_comparison_table(metrics_results)
    print("\n" + table_md + "\n")

    # 8. Save structured results
    summary_data = {
        "dataset_provenance": provenance,
        "is_synthetic": bool(df_raw.attrs.get("is_synthetic", False)),
        "total_rows_evaluated": total_eval_rows,
        "ground_truth_corruptions_count": len(ground_truth),
        "metrics": [m.to_dict() for m in metrics_results],
        "corruption_counts": counts,
        "llm_stats": llm_detector.get_stats(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    results_json_path = os.path.join(output_dir, "evaluation_results.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"[5/5] Detailed results saved to: {results_json_path}")

    return summary_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run NYC 311 Data Quality Benchmark")
    parser.add_argument("--input", type=str, default=None, help="Path to input CSV dataset")
    parser.add_argument("--sample-size", type=int, default=1000, help="Number of records to evaluate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="project_b/results", help="Output directory")

    args = parser.parse_args()
    run_benchmark(
        input_file=args.input,
        sample_size=args.sample_size,
        random_seed=args.seed,
        output_dir=args.output_dir
    )
