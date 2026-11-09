
import subprocess
import sys

print("\nRunning Project A automated tests...\n")

result = subprocess.run(
    [sys.executable, "-m", "pytest", "project_a/tests", "-v"],
    check=False
)

if result.returncode == 0:
    print("\nProject A tests completed successfully.")
else:
    print("\nProject A tests failed.")

sys.exit(result.returncode)
