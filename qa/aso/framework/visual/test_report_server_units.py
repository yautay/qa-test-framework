from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from framework.visual.report_server import (
    LOCK_TTL_SECONDS,
    _acquire_lock,
    _list_reports_payload,
    _read_results_rows,
    _report_summary,
    _safe_run_id_or_error,
    _run_id_from_visual_dir,
    _supersede_note_events,
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


class TestLocks:
    def test_acquire_lock_denies_active_lock(self, tmp_path: Path) -> None:
        build_dir = tmp_path / "artifacts" / "run-1"
        build_dir.mkdir(parents=True)

        first = _acquire_lock(build_dir, "client-a", now=1000.0)
        assert first["accepted"] is True

        second = _acquire_lock(build_dir, "client-b", now=1000.0 + LOCK_TTL_SECONDS - 1)
        assert second["accepted"] is False
        assert second["reason"] == "locked"

    def test_acquire_lock_allows_takeover_after_expiry(self, tmp_path: Path) -> None:
        build_dir = tmp_path / "artifacts" / "run-2"
        build_dir.mkdir(parents=True)

        first = _acquire_lock(build_dir, "client-a", now=2000.0)
        assert first["accepted"] is True

        second = _acquire_lock(build_dir, "client-b", now=2000.0 + LOCK_TTL_SECONDS + 1)
        assert second["accepted"] is True
        assert second["lock"]["owner_client_id"] == "client-b"


def test_supersede_note_events_marks_pending() -> None:
    outbox = [
        {"event_id": "e1", "type": "NOTE_UPSERT", "status": "pending", "test_case_id": "case-1"},
        {"event_id": "e2", "type": "BUG_SET", "status": "pending", "test_case_id": "case-1"},
        {"event_id": "e3", "type": "NOTE_UPSERT", "status": "failed", "test_case_id": "case-2"},
    ]

    _supersede_note_events(outbox, "case-1")

    assert outbox[0]["status"] == "superseded"
    assert outbox[1]["status"] == "pending"
    assert outbox[2]["status"] == "failed"
