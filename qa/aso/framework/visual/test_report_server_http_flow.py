from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlencode

import pytest

from framework.reporting.report_server.context import ReportServerContext
from framework.visual.baseline_store import BaselineStore
from qa.aso.framework.visual.report_server_http_test_helpers import (
    _env,
    _http_bytes,
    _http_json,
    _start_server,
    _stop_server,
)

pytestmark = [pytest.mark.aso]


def test_report_server_endpoints_handle_listing_results_ref_tags_and_baseline_flow(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    run_id = "20260218_120000_000001"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_dir.parent / "run-metadata.json").write_text(
        json.dumps({"tester": "jan.k", "run_note": "manual smoke"}),
        encoding="utf-8",
    )
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
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "build-metadata.json").write_text(
        json.dumps(
            {
                "visual": {
                    "excluded_count": 1,
                    "excluded_cases": [
                        {
                            "nodeid": "qa/visual/test_home.py::test_banner[fhd]",
                            "status": "failed",
                            "phase": "setup",
                            "reason": "fixture setup failed: timeout",
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    actual = report_dir / "actual" / "scenario-1.png"
    actual.parent.mkdir(parents=True)
    actual.write_bytes(b"actual-bytes")

    ui_dist = tmp_path / "ui-dist"
    ui_assets = ui_dist / "assets"
    ui_assets.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html><body>ui-shell</body></html>", encoding="utf-8")
    (ui_assets / "main.js").write_text("console.log('ok')", encoding="utf-8")

    store = BaselineStore(cast(Any, _env()), repo_root)
    source = tmp_path / "ref.png"
    source.write_bytes(b"ref-bytes")
    store.store_local_baseline("suite-1", "scenario-1", "fhd", "chromium", source)

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=store,
        run_dirs={run_id: report_dir},
    )

    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(base_url, "/api/reports")
        assert status == 200
        assert payload["reports"][0]["run_id"] == run_id
        assert payload["reports"][0]["failed"] == 1
        assert payload["reports"][0]["tester"] == "jan.k"
        assert payload["reports"][0]["run_note"] == "manual smoke"

        status, payload = _http_json(base_url, f"/api/reports/{run_id}/results")
        assert status == 200
        assert payload["build_metadata"]["visual"]["excluded_count"] == 1
        assert payload["results"][0]["scenario_id"] == "scenario-1"
        assert payload["results"][0]["tester"] == "jan.k"
        assert payload["results"][0]["run_note"] == "manual smoke"
        assert payload["results"][0]["test_metadata"]["run"]["run_id"] == run_id

        query = urlencode(
            {
                "suite_id": "suite-1",
                "scenario_id": "scenario-1",
                "viewport": "fhd",
                "browser": "chromium",
            }
        )
        status, content = _http_bytes(base_url, f"/api/reports/{run_id}/image/ref?{query}")
        assert status == 200
        assert content == b"ref-bytes"

        status, payload = _http_json(base_url, f"/api/builds/{run_id}/tags")
        assert status == 200
        assert payload["run_id"] == run_id
        assert payload["tags"]["test_cases"] == {}

        status, payload = _http_json(base_url, f"/api/reports/{run_id}/baseline/challenge", method="POST", body={})
        assert status == 200
        challenge_id = payload["challenge_id"]
        phrase = payload["phrase"]

        status, payload = _http_json(
            base_url,
            f"/api/reports/{run_id}/baseline/send",
            method="POST",
            body={
                "challenge_id": challenge_id,
                "phrase": phrase,
                "items": [
                    {
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
        assert "/candidates/" in str(payload["results"][0]["target_path"])

        status, body = _http_bytes(base_url, "/")
        assert status == 200
        assert b"ui-shell" in body

        status, body = _http_bytes(base_url, f"/reports/{run_id}")
        assert status == 200
        assert b"ui-shell" in body

        status, body = _http_bytes(base_url, f"/reports/{run_id}/actual/scenario-1.png")
        assert status == 200
        assert body == b"actual-bytes"
    finally:
        _stop_server(server, thread)


def test_baseline_send_handles_mixed_success_and_failure_and_keeps_candidates_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    run_id = "20260218_120000_000002"
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
                    },
                    {
                        "scenario_id": "scenario-2",
                        "status": "failed",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/scenario-2.png",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    actual_ok = report_dir / "actual" / "scenario-1.png"
    actual_ok.parent.mkdir(parents=True)
    actual_ok.write_bytes(b"actual-bytes-1")

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html><body>ui-shell</body></html>", encoding="utf-8")

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
        challenge_id = payload["challenge_id"]
        phrase = payload["phrase"]

        status, payload = _http_json(
            base_url,
            f"/api/reports/{run_id}/baseline/send",
            method="POST",
            body={
                "challenge_id": challenge_id,
                "phrase": phrase,
                "items": [
                    {
                        "scenario_id": "scenario-1",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/scenario-1.png",
                    },
                    {
                        "scenario_id": "scenario-2",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/missing.png",
                    },
                ],
            },
        )

        assert status == 200
        assert payload["accepted"] is False
        assert payload["saved_count"] == 1
        assert payload["failed_count"] == 1

        saved = [result for result in payload["results"] if result["status"] == "saved"]
        failed = [result for result in payload["results"] if result["status"] == "failed"]
        assert len(saved) == 1
        assert len(failed) == 1
        assert "/candidates/" in str(saved[0]["target_path"])
        assert Path(saved[0]["target_path"]).is_file()
        assert failed[0]["scenario_id"] == "scenario-2"
    finally:
        _stop_server(server, thread)


def test_results_endpoint_preserves_execution_target_base_url_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    run_id = "20260218_120000_000003"
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
                        "test_metadata": {
                            "scenario": {
                                "target_url": "/produkt/lodz",
                            },
                            "execution": {
                                "target_base_url": "https://shop.example.com",
                            },
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html><body>ui-shell</body></html>", encoding="utf-8")

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_id: report_dir},
    )

    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(base_url, f"/api/reports/{run_id}/results")
        assert status == 200

        row = payload["results"][0]
        assert row["test_metadata"]["scenario"]["target_url"] == "/produkt/lodz"
        assert row["test_metadata"]["execution"]["target_base_url"] == "https://shop.example.com"
    finally:
        _stop_server(server, thread)
