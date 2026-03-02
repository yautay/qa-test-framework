from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework.visual.report_server.reports import _read_results_rows, _report_summary

pytestmark = [pytest.mark.aso]


def test_report_summary_counts_supported_statuses() -> None:
    rows = [
        {"status": "failed"},
        {"status": "passed"},
        {"status": "new"},
        {"status": "uncertain"},
        {"status": "skipped"},
    ]

    summary = _report_summary(rows)

    assert summary == {
        "total": 5,
        "failed": 1,
        "passed": 1,
        "new": 1,
        "uncertain": 1,
        "skipped": 1,
    }


def test_read_results_rows_returns_only_dict_rows(tmp_path: Path) -> None:
    report_dir = tmp_path / "artifacts" / "20260218" / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / "results.json").write_text(
        json.dumps({"results": [{"scenario_id": "a"}, "bad", 123, {"scenario_id": "b"}]}),
        encoding="utf-8",
    )

    rows = _read_results_rows(report_dir)

    assert rows == [{"scenario_id": "a"}, {"scenario_id": "b"}]


def test_read_results_rows_returns_empty_for_missing_or_invalid_json(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)
    assert _read_results_rows(report_dir) == []

    (report_dir / "results.json").write_text("{bad json", encoding="utf-8")
    assert _read_results_rows(report_dir) == []
