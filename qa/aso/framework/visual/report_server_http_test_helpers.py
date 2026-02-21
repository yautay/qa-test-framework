from __future__ import annotations

import json
import threading
import time
from http.client import RemoteDisconnected
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from framework.visual.report_server import ReportServerContext, _build_handler


_HTTP_RETRY_ATTEMPTS = 3
_HTTP_RETRY_BACKOFF_SECONDS = 0.05


def _is_retryable_http_transport_error(exc: BaseException) -> bool:
    if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, RemoteDisconnected, TimeoutError)):
        return True
    if isinstance(exc, URLError):
        reason = exc.reason
        return isinstance(reason, (ConnectionResetError, ConnectionAbortedError, TimeoutError, OSError))
    return False


def _urlopen_with_retry(req: Request):
    last_exc: BaseException | None = None
    for attempt in range(1, _HTTP_RETRY_ATTEMPTS + 1):
        try:
            return urlopen(req)
        except HTTPError:
            raise
        except Exception as exc:  # pragma: no cover - exercised by integration tests
            if not _is_retryable_http_transport_error(exc) or attempt >= _HTTP_RETRY_ATTEMPTS:
                raise
            last_exc = exc
            time.sleep(_HTTP_RETRY_BACKOFF_SECONDS * attempt)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("unreachable")


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
    headers = {"Connection": "close"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(f"{base_url}{path}", method=method, data=data, headers=headers)
    try:
        with _urlopen_with_retry(req) as resp:
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
    req = Request(f"{base_url}{path}", method="GET", headers={"Connection": "close"})
    try:
        with _urlopen_with_retry(req) as resp:
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
    base_url = f"http://{host}:{port}"
    deadline = time.time() + 3.0
    req = Request(f"{base_url}/health", method="GET", headers={"Connection": "close"})
    while time.time() < deadline:
        try:
            with _urlopen_with_retry(req) as resp:
                if int(resp.status) == 200:
                    break
        except Exception:
            time.sleep(0.02)
    return server, base_url, thread


def _stop_server(server: ThreadingHTTPServer, thread: threading.Thread, timeout: float = 3.0) -> None:
    server.shutdown()
    thread.join(timeout=timeout)
    server.server_close()
