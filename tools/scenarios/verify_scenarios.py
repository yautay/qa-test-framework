from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.visual.scenario_loader import format_load_errors, load_scenarios_with_errors


def main() -> int:
    repo_root = REPO_ROOT
    scenarios_root = repo_root / "qa" / "visual"

    if not scenarios_root.is_dir():
        print(f"ERROR: scenarios root not found: {scenarios_root}")
        return 2

    scenario_files = sorted(scenarios_root.rglob("*.json"))
    if not scenario_files:
        print(f"ERROR: no scenario files found under: {scenarios_root}")
        return 2

    scenario_dirs = sorted({file_path.parent for file_path in scenario_files})
    total_scenarios = 0
    all_errors: list[str] = []
    seen_ids: dict[str, Path] = {}

    for scenario_dir in scenario_dirs:
        scenarios, errors = load_scenarios_with_errors(scenario_dir)
        total_scenarios += len(scenarios)

        if errors:
            formatted = format_load_errors(errors)
            all_errors.append(f"[{scenario_dir.relative_to(repo_root)}]\n{formatted}")

        for scenario in scenarios:
            previous_source = seen_ids.get(scenario.scenario_id)
            current_source = Path(scenario.source_file)
            if previous_source is not None and previous_source != current_source:
                all_errors.append(
                    "Duplicate scenario id across files: "
                    f"{scenario.scenario_id!r} in "
                    f"{previous_source.relative_to(repo_root)} and {current_source.relative_to(repo_root)}"
                )
            else:
                seen_ids[scenario.scenario_id] = current_source

    if all_errors:
        print("ERROR: visual scenarios verification failed.")
        for error in all_errors:
            print(error)
        return 2

    print(
        "OK: verified "
        f"{total_scenarios} scenarios from {len(scenario_files)} files in {len(scenario_dirs)} directories."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
