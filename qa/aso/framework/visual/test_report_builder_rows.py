from __future__ import annotations

from pathlib import Path

import pytest

from framework.visual.models import VisualResult, VisualThresholds
from framework.visual.report_builder import _build_rows

pytestmark = [pytest.mark.aso]


def test_build_rows_includes_baseline_metadata_fields(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)
    actual_path = report_dir / "actual" / "sample.png"
    baseline_path = report_dir / "ref" / "sample.png"
    diff_path = report_dir / "diff" / "sample.png"
    actual_path.parent.mkdir(parents=True)
    baseline_path.parent.mkdir(parents=True)
    diff_path.parent.mkdir(parents=True)
    actual_path.write_bytes(b"actual")
    baseline_path.write_bytes(b"baseline")
    diff_path.write_bytes(b"diff")

    result = VisualResult(
        scenario_id="scenario-1",
        status="failed",
        message="Pixel threshold exceeded",
        compare_mode="pixel",
        suite_id="suite-1",
        viewport="fhd",
        browser="chromium",
        baseline_path=str(baseline_path),
        actual_path=str(actual_path),
        diff_path=str(diff_path),
        heatmap_path="",
        pixel_changed_ratio=0.02,
        lpips=None,
        dists=None,
        thresholds=VisualThresholds(pixel_max=0.01, lpips_max=0.08, dists_max=0.08),
    )

    rows = _build_rows(report_dir, [result])

    assert len(rows) == 1
    row = rows[0]
    assert row["suite_id"] == "suite-1"
    assert row["viewport"] == "fhd"
    assert row["browser"] == "chromium"
    assert row["actual_path"] == "actual/sample.png"
    assert row["baseline_path"] == "ref/sample.png"
    assert row["diff_path"] == "diff/sample.png"
