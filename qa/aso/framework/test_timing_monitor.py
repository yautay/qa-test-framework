from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from framework.timing_monitor import load_previous_timings, save_run_timings

pytestmark = [pytest.mark.aso]


def test_load_previous_timings_uses_latest_non_empty_snapshot(tmp_path: Path) -> None:
    runs_root = tmp_path / "artifacts"
    older_run = runs_root / "20260101_120000_000001"
    newer_empty_run = runs_root / "20260101_120100_000002"
    current_run = runs_root / "20260101_120200_000003"

    save_run_timings(older_run / "logs" / "test_durations.json", {"qa/test_a.py::test_case": 1.5})
    save_run_timings(newer_empty_run / "logs" / "test_durations.json", {})
    (current_run / "logs").mkdir(parents=True, exist_ok=True)

    older_mtime = 1_000
    newer_mtime = 2_000
    current_mtime = 3_000
    # Ensure deterministic order independent of filesystem timing granularity.
    os.utime(older_run, (older_mtime, older_mtime))
    os.utime(newer_empty_run, (newer_mtime, newer_mtime))
    os.utime(current_run, (current_mtime, current_mtime))

    previous = load_previous_timings(current_run)

    assert previous == {"qa/test_a.py::test_case": 1.5}


def test_load_previous_timings_returns_empty_when_only_empty_or_invalid_exist(tmp_path: Path) -> None:
    runs_root = tmp_path / "artifacts"
    invalid_run = runs_root / "20260101_130000_000001"
    empty_run = runs_root / "20260101_130100_000002"
    current_run = runs_root / "20260101_130200_000003"

    invalid_logs = invalid_run / "logs"
    empty_logs = empty_run / "logs"
    current_logs = current_run / "logs"
    invalid_logs.mkdir(parents=True, exist_ok=True)
    empty_logs.mkdir(parents=True, exist_ok=True)
    current_logs.mkdir(parents=True, exist_ok=True)

    (invalid_logs / "test_durations.json").write_text("not-json", encoding="utf-8")
    (empty_logs / "test_durations.json").write_text(json.dumps({"cases": {}}), encoding="utf-8")

    os.utime(invalid_run, (1_000, 1_000))
    os.utime(empty_run, (2_000, 2_000))
    os.utime(current_run, (3_000, 3_000))

    previous = load_previous_timings(current_run)

    assert previous == {}
