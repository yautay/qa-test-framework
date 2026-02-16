from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qa.e2e.netcorner.nuxt.pl.app.data.scenario_catalog import build_order_smoke_scenarios


def main() -> int:
    scenarios = build_order_smoke_scenarios()
    headers = [
        "case_id",
        "legacy_group",
        "order_as",
        "delivery",
        "payment",
        "budget_s",
        "risk",
        "source_flow",
    ]
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for scenario in scenarios:
        row = [
            scenario.case.case_id,
            scenario.legacy_group,
            scenario.case.order_as.value,
            scenario.case.delivery_kind.value,
            scenario.case.payment_kind.value,
            str(scenario.max_duration_seconds),
            scenario.risk,
            scenario.source_flow,
        ]
        print("| " + " | ".join(row) + " |")
    print(f"\nTotal scenarios: {len(scenarios)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
