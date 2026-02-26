from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qa.e2e.netcorner.nuxt.pl.lib.test_data.scenario_catalog import (
    build_order_smoke_scenarios,
    collect_smoke_nodeids,
    validate_smoke_coverage,
    validate_smoke_mapping,
)


def main() -> int:
    scenarios = build_order_smoke_scenarios()
    errors = []
    errors.extend(validate_smoke_coverage(scenarios))

    collected = collect_smoke_nodeids()
    errors.extend(validate_smoke_mapping(scenarios, collected))

    if errors:
        print("Scenario verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Scenario verification passed ({len(scenarios)} scenarios).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
