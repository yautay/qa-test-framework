from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from framework.visual.baseline_store import BaselineStore
from framework.visual.report_server import ReportServerContext
from qa.aso.framework.visual.report_server_http_test_helpers import _env, _http_json, _start_server, _stop_server

pytestmark = [pytest.mark.aso]


def test_event_endpoint_is_idempotent_by_event_id(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-events"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_dir / "results.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario_id": "scenario-1",
                        "status": "failed",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/scenario-1.png",
                        "diff_path": "diff/scenario-1.png",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "actual").mkdir(parents=True)
    (report_dir / "diff").mkdir(parents=True)
    (report_dir / "actual" / "scenario-1.png").write_bytes(b"a")
    (report_dir / "diff" / "scenario-1.png").write_bytes(b"a")

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_id: report_dir},
    )
    server, base_url, thread = _start_server(context)
    try:
        case_id = "scenario-1::actual/scenario-1.png::::diff/scenario-1.png"
        status, payload = _http_json(
            base_url,
            f"/api/builds/{run_id}/events",
            method="POST",
            body={
                "event_id": "evt-1",
                "type": "BUG_SET",
                "test_case_id": case_id,
                "payload": {"note": "first"},
            },
        )
        assert status == 200
        assert payload["accepted"] is True

        status, payload = _http_json(
            base_url,
            f"/api/builds/{run_id}/events",
            method="POST",
            body={
                "event_id": "evt-1",
                "type": "BUG_SET",
                "test_case_id": case_id,
                "payload": {"note": "second"},
            },
        )
        assert status == 200
        assert payload["duplicate"] is True

        state = json.loads((report_dir.parent / "state.json").read_text(encoding="utf-8"))
        assert len(state["outbox"]) == 1
    finally:
        _stop_server(server, thread)


def test_note_events_are_rejected_as_invalid_type(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-note"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_dir / "results.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario_id": "scenario-1",
                        "status": "failed",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/scenario-1.png",
                        "diff_path": "diff/scenario-1.png",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "actual").mkdir(parents=True)
    (report_dir / "diff").mkdir(parents=True)
    (report_dir / "actual" / "scenario-1.png").write_bytes(b"a")
    (report_dir / "diff" / "scenario-1.png").write_bytes(b"a")

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_id: report_dir},
    )
    server, base_url, thread = _start_server(context)
    try:
        case_id = "scenario-1::actual/scenario-1.png::::diff/scenario-1.png"
        status, payload = _http_json(
            base_url,
            f"/api/builds/{run_id}/events",
            method="POST",
            body={
                "event_id": "note-1",
                "type": "NOTE_UPSERT",
                "test_case_id": case_id,
                "payload": {"note": "first"},
            },
        )
        assert status == 400
        assert payload["error"] == "invalid event type"
    finally:
        _stop_server(server, thread)


def test_event_endpoint_rejects_bug_note_over_limit(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-limit"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_dir / "results.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario_id": "scenario-1",
                        "status": "failed",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/scenario-1.png",
                        "diff_path": "diff/scenario-1.png",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_id: report_dir},
    )
    server, base_url, thread = _start_server(context)
    try:
        case_id = "scenario-1::actual/scenario-1.png::::diff/scenario-1.png"
        status, payload = _http_json(
            base_url,
            f"/api/builds/{run_id}/events",
            method="POST",
            body={
                "event_id": "note-long",
                "type": "BUG_SET",
                "test_case_id": case_id,
                "payload": {"note": "a" * 501},
            },
        )
        assert status == 400
        assert "500" in payload["error"]
    finally:
        _stop_server(server, thread)
