from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from qa.aso.framework.visual.report_server_http_test_helpers import _http_json

pytestmark = [pytest.mark.aso]


def test_http_json_raises_for_empty_success_body() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        with pytest.raises(AssertionError, match=r"^Empty JSON response body for GET /empty \(status=200\)$"):
            _http_json(base_url, "/empty")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_json_raises_for_empty_error_body() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        with pytest.raises(AssertionError, match=r"^Empty JSON error body for GET /empty \(status=400\)$"):
            _http_json(base_url, "/empty")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
