from __future__ import annotations

import json
from pathlib import Path


def save_run_timings(file_path: Path, timings: dict[str, float]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cases": dict(sorted(timings.items()))}
    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def load_previous_timings(current_run_dir: Path) -> dict[str, float]:
    runs_root = current_run_dir.parent
    run_dirs = sorted([p for p in runs_root.iterdir() if p.is_dir() and p.name != current_run_dir.name])
    if not run_dirs:
        return {}
    latest = run_dirs[-1]
    candidate = latest / "logs" / "test_durations.json"
    if not candidate.exists():
        return {}
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return {}
    cases = payload.get("cases", {})
    return {k: float(v) for k, v in cases.items()}


def detect_slow_regressions(
    current: dict[str, float],
    previous: dict[str, float],
    threshold_ratio: float = 0.2,
) -> list[dict[str, float | str]]:
    regressions: list[dict[str, float | str]] = []
    for nodeid, current_time in current.items():
        previous_time = previous.get(nodeid)
        if not previous_time or previous_time <= 0:
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
    return regressions
