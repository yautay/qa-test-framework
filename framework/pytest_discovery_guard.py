from __future__ import annotations

import os
import re
import subprocess
import sys


def main() -> int:
    min_expected = int(os.getenv("MIN_EXPECTED_TESTS", "1"))
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"(\d+) tests? collected", output)
    collected = int(match.group(1)) if match else 0

    if collected == 0:
        print("ERROR: pytest collected 0 tests. Check testpaths/discovery patterns.")
        print(output)
        return 2

    if collected < min_expected:
        print(f"ERROR: collected {collected} tests, below MIN_EXPECTED_TESTS={min_expected}.")
        print(output)
        return 3

    print(f"OK: collected {collected} tests (threshold {min_expected}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
