from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework.visual.report_builder import _clear_ready_marker, _write_ready_marker

pytestmark = [pytest.mark.aso]


def test_write_ready_marker_creates_ready_payload(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)

    _write_ready_marker(report_dir, [{"scenario_id": "a"}, {"scenario_id": "b"}])

    marker = report_dir / ".report-ready.json"
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["ready"] is True
    assert payload["results_count"] == 2
    assert isinstance(payload.get("generated_at_utc"), str)


def test_clear_ready_marker_removes_existing_file(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)
    marker = report_dir / ".report-ready.json"
    marker.write_text('{"ready": true}\n', encoding="utf-8")

    _clear_ready_marker(report_dir)

    assert not marker.exists()
