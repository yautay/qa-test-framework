from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from framework.visual.report_server import (
    _had_previous_failures,
    _list_reports_payload,
    _read_last_audit_entry,
    _read_results_rows,
    _report_summary,
    _safe_run_id_or_error,
    _run_id_from_visual_dir,
    ReportServerContext,
)

pytestmark = [pytest.mark.aso]


class _DummyBaselineStore:
    def resolve_baseline(self, *_args):
        return None


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


def test_safe_run_id_accepts_alnum_dot_dash_underscore() -> None:
    assert _safe_run_id_or_error("2026.02-18_001") == "2026.02-18_001"


@pytest.mark.parametrize("raw", ["", "../evil", "a/b", "a b", "%2Fetc"])
def test_safe_run_id_rejects_unsafe_values(raw: str) -> None:
    with pytest.raises(ValueError, match="invalid run_id"):
        _safe_run_id_or_error(raw)


def test_run_id_from_visual_dir_falls_back_to_parent_when_outside_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    report_dir = tmp_path / "custom report"
    report_dir.mkdir(parents=True)

    run_id = _run_id_from_visual_dir(repo_root, report_dir)

    assert run_id
    assert " " not in run_id
    assert "/" not in run_id


def test_list_reports_payload_includes_stats_and_sorted_desc(tmp_path: Path) -> None:
    run_a = tmp_path / "artifacts" / "20260217" / "visual"
    run_b = tmp_path / "artifacts" / "20260218" / "visual"
    ui_dist = tmp_path / "ui"
    ui_dist.mkdir()
    run_a.mkdir(parents=True)
    run_b.mkdir(parents=True)
    (run_a / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (run_b / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")

    (run_a / "results.json").write_text(json.dumps({"results": [{"status": "failed"}]}), encoding="utf-8")
    (run_b / "results.json").write_text(
        json.dumps(
            {
                "results": [
                    {"status": "passed"},
                    {"status": "new"},
                    {"status": "uncertain"},
                    {"status": "skipped"},
                ]
            }
        ),
        encoding="utf-8",
    )

    context = ReportServerContext(
        repo_root=tmp_path,
        ui_dist_dir=ui_dist,
        baseline_store=cast(Any, _DummyBaselineStore()),
        run_dirs={"20260217": run_a, "20260218": run_b},
    )

    payload = _list_reports_payload(context)

    assert [item["run_id"] for item in payload] == ["20260218", "20260217"]
    assert payload[0]["total"] == 4
    assert payload[0]["passed"] == 1
    assert payload[0]["new"] == 1
    assert payload[0]["uncertain"] == 1
    assert payload[0]["skipped"] == 1
    assert payload[0]["tester"] == ""
    assert payload[0]["run_note"] == ""
    assert payload[1]["failed"] == 1


def test_list_reports_payload_skips_runs_without_ready_marker(tmp_path: Path) -> None:
    run_dir = tmp_path / "artifacts" / "20260218" / "visual"
    ui_dist = tmp_path / "ui"
    ui_dist.mkdir()
    run_dir.mkdir(parents=True)
    (run_dir / "results.json").write_text(json.dumps({"results": [{"status": "failed"}]}), encoding="utf-8")

    context = ReportServerContext(
        repo_root=tmp_path,
        ui_dist_dir=ui_dist,
        baseline_store=cast(Any, _DummyBaselineStore()),
        run_dirs={"20260218": run_dir},
    )

    payload = _list_reports_payload(context)

    assert payload == []


def test_list_reports_payload_picks_new_run_after_server_context_created(tmp_path: Path) -> None:
    ui_dist = tmp_path / "ui"
    ui_dist.mkdir()
    context = ReportServerContext(
        repo_root=tmp_path,
        ui_dist_dir=ui_dist,
        baseline_store=cast(Any, _DummyBaselineStore()),
        run_dirs={},
    )

    assert _list_reports_payload(context) == []

    run_dir = tmp_path / "artifacts" / "20260219" / "visual"
    run_dir.mkdir(parents=True)
    (run_dir / "results.json").write_text(json.dumps({"results": [{"status": "passed"}]}), encoding="utf-8")
    (run_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")

    payload = _list_reports_payload(context)

    assert [item["run_id"] for item in payload] == ["20260219"]


class TestReadLastAuditEntry:
    def test_returns_none_when_no_audit_file(self, tmp_path: Path) -> None:
        result = _read_last_audit_entry(tmp_path)
        assert result is None

    def test_returns_none_when_file_empty(self, tmp_path: Path) -> None:
        audit_file = tmp_path / "reporting-audit.json"
        audit_file.write_text("", encoding="utf-8")
        result = _read_last_audit_entry(tmp_path)
        assert result is None

    def test_returns_none_when_file_invalid_json(self, tmp_path: Path) -> None:
        audit_file = tmp_path / "reporting-audit.json"
        audit_file.write_text("not valid json", encoding="utf-8")
        result = _read_last_audit_entry(tmp_path)
        assert result is None

    def test_returns_last_entry_from_list(self, tmp_path: Path) -> None:
        audit_file = tmp_path / "reporting-audit.json"
        audit_file.write_text(
            json.dumps(
                [
                    {"timestamp_utc": "2026-02-20T10:00:00Z", "bug": {"sent": 1}},
                    {"timestamp_utc": "2026-02-20T11:00:00Z", "bug": {"sent": 2}},
                ]
            ),
            encoding="utf-8",
        )
        result = _read_last_audit_entry(tmp_path)
        assert result is not None
        assert result["timestamp_utc"] == "2026-02-20T11:00:00Z"

    def test_returns_none_when_list_empty(self, tmp_path: Path) -> None:
        audit_file = tmp_path / "reporting-audit.json"
        audit_file.write_text(json.dumps([]), encoding="utf-8")
        result = _read_last_audit_entry(tmp_path)
        assert result is None


class TestHadPreviousFailures:
    def test_returns_false_when_none(self) -> None:
        assert _had_previous_failures(None) is False

    def test_returns_false_when_no_failures(self) -> None:
        audit = {
            "bug": {"sent": 1, "failed": 0},
            "aso": {"sent": 1, "failed": 0},
            "note": {"sent": 1, "failed": 0},
        }
        assert _had_previous_failures(audit) is False

    def test_returns_true_when_bug_failed(self) -> None:
        audit = {
            "bug": {"sent": 0, "failed": 1},
            "aso": {"sent": 1, "failed": 0},
            "note": {"sent": 1, "failed": 0},
        }
        assert _had_previous_failures(audit) is True

    def test_returns_true_when_aso_failed(self) -> None:
        audit = {
            "bug": {"sent": 1, "failed": 0},
            "aso": {"sent": 0, "failed": 1},
            "note": {"sent": 1, "failed": 0},
        }
        assert _had_previous_failures(audit) is True

    def test_returns_true_when_note_failed(self) -> None:
        audit = {
            "bug": {"sent": 1, "failed": 0},
            "aso": {"sent": 1, "failed": 0},
            "note": {"sent": 0, "failed": 1},
        }
        assert _had_previous_failures(audit) is True

    def test_returns_false_when_missing_keys(self) -> None:
        audit = {"bug": {}}
        assert _had_previous_failures(audit) is False

    def test_returns_false_when_empty_dict(self) -> None:
        assert _had_previous_failures({}) is False
