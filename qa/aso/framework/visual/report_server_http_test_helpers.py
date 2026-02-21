from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from framework.visual.report_server import ReportServerContext, _build_handler


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
            raw = resp.read()
            if not raw:
                raise AssertionError(f"Empty JSON response body for {method} {path} (status={int(resp.status)})")
            payload = json.loads(raw.decode("utf-8"))
            return int(resp.status), payload
    except HTTPError as exc:
        raw = exc.read()
        if not raw:
            raise AssertionError(f"Empty JSON error body for {method} {path} (status={int(exc.code)})")
        payload = json.loads(raw.decode("utf-8"))
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
