from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from framework.visual.baseline_store import BaselineStore
from framework.visual.report_server import ReportServerContext
from qa.aso.framework.visual.report_server_http_test_helpers import _env, _http_json, _start_server, _stop_server

pytestmark = [pytest.mark.aso]


def test_report_server_reports_sync_issue_counters_on_reports_list(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    run_id = "run-sync"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_dir / "results.json").write_text(json.dumps({"results": []}), encoding="utf-8")

    state = {
        "test_cases": {
            "case-a": {
                "bug": {"locked": True, "synced": False, "note": ""},
                "aso": {"locked": False, "synced": False, "note": ""},
            },
            "case-b": {
                "bug": {"locked": False, "synced": True, "note": ""},
                "aso": {"locked": True, "synced": False, "note": ""},
            },
        },
        "outbox": [
            {"event_id": "e1", "type": "BUG_SET", "status": "failed", "test_case_id": "case-a"},
            {"event_id": "e2", "type": "ASO_SET", "status": "pending", "test_case_id": "case-b"},
            {"event_id": "e3", "type": "BUG_SET", "status": "sending", "test_case_id": "case-a"},
            {"event_id": "e4", "type": "NOTE_SET", "status": "failed", "test_case_id": "case-a"},
        ],
    }
    (report_dir.parent / "state.json").write_text(json.dumps(state), encoding="utf-8")

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_id: report_dir},
        reporting_enabled=True,
    )
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(base_url, "/api/reports")
        assert status == 200
        report = payload["reports"][0]
        assert report["run_id"] == run_id
        assert report["has_sync_issues"] is True
        assert report["sync_failed_count"] == 1
        assert report["sync_pending_count"] == 1
        assert report["sync_sending_count"] == 1
        assert report["sync_unsynced_count"] == 2
        assert report["pms_total_count"] == 0
        assert report["pms_pending_count"] == 0
        assert report["pms_success_count"] == 0
        assert report["pms_error_count"] == 0
    finally:
        _stop_server(server, thread)
