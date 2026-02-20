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
from framework.visual.report_server import ReportServerContext, _build_handler

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

        status, payload = _http_json(base_url, f"/api/builds/{run_id}/state")
        assert status == 200
        assert payload["run_id"] == run_id
        assert payload["state"]["test_cases"] == {}

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
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


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
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


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
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_note_events_supersede_previous(tmp_path: Path) -> None:
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
        _http_json(
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
        _http_json(
            base_url,
            f"/api/builds/{run_id}/events",
            method="POST",
            body={
                "event_id": "note-2",
                "type": "NOTE_UPSERT",
                "test_case_id": case_id,
                "payload": {"note": "second"},
            },
        )

        state = json.loads((report_dir.parent / "state.json").read_text(encoding="utf-8"))
        statuses = [entry["status"] for entry in state["outbox"]]
        assert "superseded" in statuses
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_report_endpoint_flushes_and_generates_pdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeReportingClient:
        def __init__(self):
            self.calls: list[tuple[str, dict[str, Any]]] = []

        def send_payload(self, endpoint: str, payload: dict[str, Any]) -> bool:
            self.calls.append((endpoint, payload))
            return True

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-flush"
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

    case_id = "scenario-1::actual/scenario-1.png::::diff/scenario-1.png"
    state_path = report_dir.parent / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "test_cases": {
                    case_id: {
                        "bug": {"locked": True, "synced": False},
                        "aso": {"locked": False, "synced": False},
                        "note": {"content": "", "synced": False},
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
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    fake_client = _FakeReportingClient()
    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={run_id: report_dir},
        reporting_client=cast(Any, fake_client),
        reporting_bug_endpoint="/bug",
    )

    monkeypatch.setattr(
        "framework.visual.report_server._generate_bug_pdf",
        lambda **_kwargs: ("/tmp/report.pdf", 1),
    )

    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(base_url, f"/api/builds/{run_id}/report", method="POST", body={})
        assert status == 200
        assert payload["pdf"]["pages"] == 1

        state = json.loads((report_dir.parent / "state.json").read_text(encoding="utf-8"))
        assert state["outbox"][0]["status"] == "sent"
        assert state["test_cases"][case_id]["bug"]["synced"] is True
        assert fake_client.calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_event_endpoint_rejects_note_over_limit(tmp_path: Path) -> None:
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
                "type": "NOTE_UPSERT",
                "test_case_id": case_id,
                "payload": {"note": "a" * 201},
            },
        )
        assert status == 400
        assert "200" in payload["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
