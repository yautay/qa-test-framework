from __future__ import annotations

"""Persist and analyze recorded test durations to flag slowdowns."""

import json
import math
from json import JSONDecodeError
from pathlib import Path


def save_run_timings(file_path: Path, timings: dict[str, float]) -> None:
    """Store the current run durations as JSON for future comparison."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Keep stable ordering for readable diffs
    payload = {"cases": dict(sorted(timings.items()))}

    file_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_previous_timings(current_run_dir: Path) -> dict[str, float]:
    """Load the most recent persisted timings from previous runs, if available.

    Strategy:
    - look at sibling run directories
    - pick the most recently modified one
    - read logs/test_durations.json
    - safely coerce values to float
    """
    runs_root = current_run_dir.parent
    if not runs_root.exists():
        return {}

    run_dirs = [
        p
        for p in runs_root.iterdir()
        if p.is_dir() and p.name != current_run_dir.name
    ]
    if not run_dirs:
        return {}

    # More robust than lexicographic sorting of directory names
    latest = max(run_dirs, key=lambda p: p.stat().st_mtime)

    candidate = latest / "logs" / "test_durations.json"
    if not candidate.is_file():
        return {}

    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, JSONDecodeError):
        return {}

    cases = payload.get("cases", {})
    if not isinstance(cases, dict):
        return {}

    out: dict[str, float] = {}
    for k, v in cases.items():
        if not isinstance(k, str):
            continue
        try:
            val = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(val):
            out[k] = val

    return out


def detect_slow_regressions(
    current: dict[str, float],
    previous: dict[str, float],
    threshold_ratio: float = 0.2,
) -> list[dict[str, float | str]]:
    """Compare runs and report regressions that exceed the threshold ratio.

    A regression is reported when:
        (current - previous) / previous > threshold_ratio
    """
    regressions: list[dict[str, float | str]] = []

    for nodeid, current_time_raw in current.items():
        try:
            current_time = float(current_time_raw)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(current_time) or current_time <= 0:
            continue

        previous_time_raw = previous.get(nodeid)
        if previous_time_raw is None:
            continue

        try:
            previous_time = float(previous_time_raw)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(previous_time) or previous_time <= 0:
            continue

        ratio = (current_time - previous_time) / previous_time

        if ratio > threshold_ratio:
            regressions.append(
                {
                    "nodeid": nodeid,
                    "previous_seconds": round(previous_time, 3),
                    "current_seconds": round(current_time, 3),
                    "increase_ratio": round(ratio, 3),
                }
            )

    # Most severe regressions first
    regressions.sort(key=lambda r: r["increase_ratio"], reverse=True)

    return regressions
