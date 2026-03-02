from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from framework.visual.baseline_store import BaselineStore
from framework.reporting.report_server.context import ReportServerContext
from qa.aso.framework.reporting.report_server_http_test_helpers import _env, _http_json, _start_server, _stop_server

pytestmark = [pytest.mark.aso]


def test_reporting_disabled_treats_sync_as_success_for_frontend(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-disabled"
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
        reporting_enabled=False,
    )
    server, base_url, thread = _start_server(context)
    try:
        case_id = "scenario-1::actual/scenario-1.png::::diff/scenario-1.png"
        status, payload = _http_json(
            base_url,
            f"/api/builds/{run_id}/events",
            method="POST",
            body={
                "event_id": "evt-disabled-1",
                "type": "BUG_SET",
                "test_case_id": case_id,
                "payload": {"note": "offline"},
            },
        )
        assert status == 200
        assert payload["event"]["status"] == "sent"

        status, payload = _http_json(base_url, f"/api/builds/{run_id}/tags")
        assert status == 200
        state = payload["tags"]
        assert state["test_cases"][case_id]["bug"]["synced"] is True
        assert state["outbox"][0]["status"] == "sent"

        status, payload = _http_json(base_url, "/api/reports")
        assert status == 200
        report = payload["reports"][0]
        assert report["has_sync_issues"] is False
        assert report["sync_failed_count"] == 0
        assert report["sync_pending_count"] == 0
        assert report["sync_sending_count"] == 0
        assert report["sync_unsynced_count"] == 0
    finally:
        _stop_server(server, thread)


def test_report_endpoint_logs_single_skip_entry_when_reporting_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-disabled-report"
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

    case_id = "scenario-1::actual/scenario-1.png::::diff/scenario-1.png"
    (report_dir.parent / "state.json").write_text(
        json.dumps(
            {
                "test_cases": {
                    case_id: {
                        "bug": {"locked": True, "synced": False},
                        "aso": {"locked": False, "synced": False},
                    }
                },
                "outbox": [
                    {
                        "event_id": "evt-1",
                        "type": "BUG_SET",
                        "payload": {},
                        "status": "failed",
                        "attempts": 1,
                        "last_attempt_at": "",
                        "sent_at": "",
                        "last_error": "error",
                        "test_case_id": case_id,
                    },
                    {
                        "event_id": "evt-2",
                        "type": "ASO_SET",
                        "payload": {},
                        "status": "pending",
                        "attempts": 0,
                        "last_attempt_at": "",
                        "sent_at": "",
                        "last_error": "",
                        "test_case_id": case_id,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")

    monkeypatch.setattr("framework.reporting.report_server.services.pdf._generate_bug_pdf", lambda **_kwargs: ("/tmp/report.pdf", 1))
    logged: list[tuple[str, dict[str, Any]]] = []

    def _debug(msg: str, **kwargs: Any) -> None:
        logged.append((msg, kwargs))

    monkeypatch.setattr("framework.reporting.report_server.services.sync.logger.debug", _debug)

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_id: report_dir},
        reporting_enabled=False,
    )
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(base_url, f"/api/builds/{run_id}/report", method="POST", body={})
        assert status == 200
        assert payload["pdf"]["pages"] == 1

        skip_logs = [
            item
            for item in logged
            if item[0] == "reporting_api_disabled_skipping_sync" and item[1].get("source") == "report_flush"
        ]
        assert len(skip_logs) == 1
        assert skip_logs[0][1].get("events_count") == 2

        state = json.loads((report_dir.parent / "state.json").read_text(encoding="utf-8"))
        assert all(entry["status"] == "sent" for entry in state["outbox"])
        assert state["test_cases"][case_id]["bug"]["synced"] is True
    finally:
        _stop_server(server, thread)


def test_state_endpoint_normalizes_legacy_unsynced_state_when_reporting_disabled(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-disabled-state"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_dir / "results.json").write_text(json.dumps({"results": []}), encoding="utf-8")

    case_id = "case-legacy"
    (report_dir.parent / "state.json").write_text(
        json.dumps(
            {
                "test_cases": {
                    case_id: {
                        "bug": {"locked": True, "synced": False, "note": ""},
                        "aso": {"locked": True, "synced": False, "note": ""},
                    }
                },
                "outbox": [
                    {
                        "event_id": "legacy-1",
                        "type": "BUG_SET",
                        "payload": {},
                        "status": "pending",
                        "attempts": 0,
                        "last_attempt_at": "",
                        "sent_at": "",
                        "last_error": "",
                        "test_case_id": case_id,
                    },
                    {
                        "event_id": "legacy-2",
                        "type": "ASO_SET",
                        "payload": {},
                        "status": "failed",
                        "attempts": 1,
                        "last_attempt_at": "",
                        "sent_at": "",
                        "last_error": "timeout",
                        "test_case_id": case_id,
                    },
                ],
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
        reporting_enabled=False,
    )
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(base_url, f"/api/builds/{run_id}/tags")
        assert status == 200
        state = payload["tags"]
        assert state["test_cases"][case_id]["bug"]["synced"] is True
        assert state["test_cases"][case_id]["aso"]["synced"] is True
        assert all(entry["status"] == "sent" for entry in state["outbox"])

        status, payload = _http_json(base_url, "/api/reports")
        assert status == 200
        report = payload["reports"][0]
        assert report["has_sync_issues"] is False
        assert report["sync_unsynced_count"] == 0
    finally:
        _stop_server(server, thread)
