from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from framework.visual.baseline_store import BaselineStore
from tools.visual.report_server import ReportServerContext, _build_handler

pytestmark = [pytest.mark.aso]


def _env() -> SimpleNamespace:
    return SimpleNamespace(
        visual_cache_dir=".visual_cache",
        visual_baseline_provider="local",
        visual_baseline_profile="test-ref",
        visual_baseline_version="latest",
        visual_minio_endpoint="",
        visual_minio_access_key="",
        visual_minio_secret_key="",
        visual_minio_secure=False,
        visual_minio_bucket="visual-baselines",
    )


def _http_json(base_url: str, path: str, method: str = "GET", body: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{base_url}{path}", method=method, data=data, headers=headers)
    try:
        with urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8") or "{}")
            return int(resp.status), payload
    except HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8") or "{}")
        return int(exc.code), payload


def _http_bytes(base_url: str, path: str) -> tuple[int, bytes]:
    req = Request(f"{base_url}{path}", method="GET")
    try:
        with urlopen(req) as resp:
            return int(resp.status), resp.read()
    except HTTPError as exc:
        return int(exc.code), exc.read()


def _start_server(context: ReportServerContext) -> tuple[ThreadingHTTPServer, str, threading.Thread]:
    handler = _build_handler(context)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = server.server_address[0]
    port = server.server_address[1]
    return server, f"http://{host}:{port}", thread


def test_report_server_endpoints_handle_listing_results_ref_tags_and_baseline_flow(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    run_id = "20260218_120000_000001"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
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

        status, payload = _http_json(base_url, f"/api/reports/{run_id}/results")
        assert status == 200
        assert payload["results"][0]["scenario_id"] == "scenario-1"

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

        status, _payload = _http_json(
            base_url, f"/reports/{run_id}/vrt-tags.json", method="PUT", body={"k": {"bug": True}}
        )
        assert status == 200
        assert (report_dir / "vrt-tags.json").is_file()

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
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_report_server_rejects_challenge_run_mismatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_a = "run-a"
    run_b = "run-b"
    report_a = repo_root / "artifacts" / run_a / "visual"
    report_b = repo_root / "artifacts" / run_b / "visual"
    report_a.mkdir(parents=True)
    report_b.mkdir(parents=True)

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
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_report_server_ref_endpoint_validates_query_and_run(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-1"
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)

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
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
