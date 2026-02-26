from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework.visual.models import VisualResult
from framework.visual.report_builder import write_visual_results_json

pytestmark = [pytest.mark.aso]


def test_write_visual_results_json_writes_results_atomically(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    baseline = report_dir / "baseline.png"
    actual = report_dir / "actual.png"
    report_dir.mkdir(parents=True)
    baseline.write_bytes(b"baseline")
    actual.write_bytes(b"actual")

    rows = [
        VisualResult(
            scenario_id="hero",
            status="passed",
            message="ok",
            compare_mode="perceptual",
            baseline_path=str(baseline),
            actual_path=str(actual),
            suite_id="suite",
            viewport="fhd",
            browser="chromium",
            perceptual={"status": "queued", "job_id": "job-1"},
        )
    ]

    write_visual_results_json(report_dir, rows)

    payload = json.loads((report_dir / "results.json").read_text(encoding="utf-8"))
    assert len(payload["results"]) == 1
    assert payload["results"][0]["scenario_id"] == "hero"
    assert payload["results"][0]["perceptual"]["status"] == "queued"
    assert not (report_dir / "results.json.tmp").exists()
