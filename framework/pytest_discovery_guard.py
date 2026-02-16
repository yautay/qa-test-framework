from __future__ import annotations

"""Guard that verifies pytest collects a minimum number of tests before running."""

import os
import re
import subprocess
import sys


def main() -> int:
    """Check pytest collection count and exit non-zero when expectations fail."""

    min_expected = int(os.getenv("MIN_EXPECTED_TESTS", "1"))

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            check=False,
            timeout=int(os.getenv("PYTEST_COLLECT_TIMEOUT_SECONDS", "120")),
        )
    except subprocess.TimeoutExpired:
        print("ERROR: pytest collection timed out.")
        return 4
    except OSError as e:
        print(f"ERROR: failed to start pytest: {e}")
        return 5

    output = f"{result.stdout}\n{result.stderr}".strip()

    # If pytest itself errored, surface that explicitly (often ImportError during collection).
    if result.returncode != 0:
        # Still try to extract collected count if present (sometimes pytest reports it before error).
        match = re.search(r"(\d+)\s+tests?\s+collected", output)
        collected = int(match.group(1)) if match else 0

        print(f"ERROR: pytest collection failed (exit code {result.returncode}).")
        if output:
            print(output)

        # Preserve your semantics: treat "0 collected" as the main signal, but distinguish failure code.
        return 2 if collected == 0 else 6

    match = re.search(r"(\d+)\s+tests?\s+collected", output)
    collected = int(match.group(1)) if match else 0

    if collected == 0:
        print("ERROR: pytest collected 0 tests. Check testpaths/discovery patterns.")
        if output:
            print(output)
        return 2

    if collected < min_expected:
        print(f"ERROR: collected {collected} tests, below MIN_EXPECTED_TESTS={min_expected}.")
        if output:
            print(output)
        return 3

    print(f"OK: collected {collected} tests (threshold {min_expected}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
