from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from framework.reporting.report_server.context import ReportServerContext
from framework.visual.baseline_store import BaselineStore
from qa.aso.framework.visual.report_server_http_test_helpers import _env, _http_json, _start_server, _stop_server

pytestmark = [pytest.mark.aso]


def test_report_server_rejects_challenge_run_mismatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_a = "run-a"
    run_b = "run-b"
    report_a = repo_root / "artifacts" / run_a / "visual"
    report_b = repo_root / "artifacts" / run_b / "visual"
    report_a.mkdir(parents=True)
    report_b.mkdir(parents=True)
    (report_a / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_b / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_a: report_a, run_b: report_b},
    )
    server, base_url, thread = _start_server(context)

    try:
        status, payload = _http_json(base_url, f"/api/reports/{run_a}/baseline/challenge", method="POST", body={})
        assert status == 200
        challenge_id = payload["challenge_id"]
        phrase = payload["phrase"]

        status, payload = _http_json(
            base_url,
            f"/api/reports/{run_b}/baseline/send",
            method="POST",
            body={"challenge_id": challenge_id, "phrase": phrase, "items": []},
        )
        assert status == 403
        assert "run mismatch" in payload["error"]
    finally:
        _stop_server(server, thread)


def test_report_server_ref_endpoint_validates_query_and_run(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-1"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")

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
        status, payload = _http_json(base_url, f"/api/reports/{run_id}/image/ref")
        assert status == 400
        assert "missing required query params" in payload["error"]

        status, payload = _http_json(
            base_url,
            "/api/reports/missing-run/image/ref?suite_id=s&scenario_id=x&viewport=v&browser=b",
        )
        assert status == 404
        assert payload["error"] == "report not found"
    finally:
        _stop_server(server, thread)


def test_baseline_send_clears_baseline_flag_in_state_for_sent_case(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-baseline-clear"
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
                        "diff_path": "",
                        "baseline_path": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "actual").mkdir(parents=True)
    (report_dir / "actual" / "scenario-1.png").write_bytes(b"a")

    case_id = "scenario-1::actual/scenario-1.png::::"
    (report_dir.parent / "state.json").write_text(
        json.dumps(
            {
                "test_cases": {
                    case_id: {
                        "bug": {"locked": False, "synced": False, "note": ""},
                        "aso": {"locked": False, "synced": False, "note": ""},
                        "baseline": True,
                    }
                },
                "outbox": [],
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
        status, payload = _http_json(base_url, f"/api/reports/{run_id}/baseline/challenge", method="POST", body={})
        assert status == 200

        status, payload = _http_json(
            base_url,
            f"/api/reports/{run_id}/baseline/send",
            method="POST",
            body={
                "challenge_id": payload["challenge_id"],
                "phrase": payload["phrase"],
                "items": [
                    {
                        "case_id": case_id,
                        "scenario_id": "scenario-1",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/scenario-1.png",
                    }
                ],
            },
        )
        assert status == 200
        assert payload["saved_count"] == 1

        state = json.loads((report_dir.parent / "state.json").read_text(encoding="utf-8"))
        assert state["test_cases"][case_id]["baseline"] is False
    finally:
        _stop_server(server, thread)
