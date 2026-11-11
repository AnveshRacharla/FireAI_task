"""
Project B: NYC 311 Data Quality Engine - Master Reproducibility Script.
Runs the complete benchmark suite, evaluates all 4 detectors and the hybrid pipeline,
executes automated pytest tests, and generates the empirical summary.
"""

import sys
import subprocess
import time
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).parent.resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from project_b.benchmark import run_benchmark


def main():
    print("=" * 80)
    print("PROJECT B: NYC 311 DATA QUALITY ENGINE - ONE-COMMAND REPRODUCIBILITY")
    print("=" * 80)
    start_total = time.perf_counter()

    # Step 1: Run automated tests
    print("\n>>> STEP 1: Running Project B test suite via pytest...")
    test_res = subprocess.run(
        [sys.executable, "-m", "pytest", "project_b/tests", "-v"],
        cwd=str(WORKSPACE_ROOT),
        check=False
    )
    if test_res.returncode != 0:
        print("\n[FAIL] Project B tests failed. Aborting benchmark.")
        sys.exit(test_res.returncode)
    print("\n[PASS] All Project B automated tests passed successfully.")

    # Step 2: Run benchmark & evaluation
    print("\n>>> STEP 2: Running NYC 311 evaluation benchmark...")
    summary = run_benchmark(
        sample_size=1000,
        random_seed=42,
        output_dir="project_b/results"
    )

    total_duration = time.perf_counter() - start_total
    print("=" * 80)
    print(f"PROJECT B RUN COMPLETED IN {total_duration:.2f} SECONDS")
    print(f"Results saved to: {WORKSPACE_ROOT / 'project_b' / 'results' / 'evaluation_results.json'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
