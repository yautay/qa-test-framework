from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from framework.visual.report_server.context import ReportServerContext
from framework.visual.report_server.reports import _list_reports_payload

pytestmark = [pytest.mark.aso]


class _DummyBaselineStore:
    def resolve_baseline(self, *_args):
        return None


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


def test_list_reports_payload_clears_sync_issue_counts_when_reporting_disabled(tmp_path: Path) -> None:
    run_dir = tmp_path / "artifacts" / "20260220" / "visual"
    ui_dist = tmp_path / "ui"
    ui_dist.mkdir()
    run_dir.mkdir(parents=True)
    (run_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (run_dir / "results.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    (run_dir.parent / "state.json").write_text(
        json.dumps(
            {
                "test_cases": {
                    "case-1": {
                        "bug": {"locked": True, "synced": False, "note": ""},
                        "aso": {"locked": True, "synced": False, "note": ""},
                    }
                },
                "outbox": [
                    {"event_id": "e1", "type": "BUG_SET", "status": "pending", "test_case_id": "case-1"},
                    {"event_id": "e2", "type": "ASO_SET", "status": "failed", "test_case_id": "case-1"},
                ],
            }
        ),
        encoding="utf-8",
    )

    context = ReportServerContext(
        repo_root=tmp_path,
        ui_dist_dir=ui_dist,
        baseline_store=cast(Any, _DummyBaselineStore()),
        run_dirs={"20260220": run_dir},
        reporting_enabled=False,
    )

    payload = _list_reports_payload(context)

    assert len(payload) == 1
    report = payload[0]
    assert report["has_sync_issues"] is False
    assert report["sync_unsynced_count"] == 0
    assert report["sync_failed_count"] == 0
    assert report["sync_pending_count"] == 0
    assert report["sync_sending_count"] == 0


def test_list_reports_payload_includes_perceptual_status_from_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "artifacts" / "20260221" / "visual"
    ui_dist = tmp_path / "ui"
    ui_dist.mkdir()
    run_dir.mkdir(parents=True)
    (run_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (run_dir / "results.json").write_text(json.dumps({"results": []}), encoding="utf-8")
    (run_dir / "perceptual-status.json").write_text(
        json.dumps(
            {
                "total_count": 10,
                "pending_count": 3,
                "done_count": 6,
                "error_count": 1,
                "in_progress": True,
            }
        ),
        encoding="utf-8",
    )

    context = ReportServerContext(
        repo_root=tmp_path,
        ui_dist_dir=ui_dist,
        baseline_store=cast(Any, _DummyBaselineStore()),
        run_dirs={"20260221": run_dir},
    )

    payload = _list_reports_payload(context)

    assert len(payload) == 1
    report = payload[0]
    assert report["pms_total_count"] == 10
    assert report["pms_pending_count"] == 3
    assert report["pms_success_count"] == 6
    assert report["pms_error_count"] == 1
    assert report["pms_in_progress"] is True
