from __future__ import annotations

from pathlib import Path
import time
from typing import Any, cast

import pytest
import requests

from framework.env import load_env
from framework.reporting_client import ReportingClient

pytestmark = [pytest.mark.aso]


class _OkResponse:
    ok = True
    status_code = 200


def test_reporting_client_skips_calls_when_disabled() -> None:
    calls: list[tuple[str, dict]] = []

    class _FakeSession:
        def __init__(self, sink: list[tuple[str, dict]]) -> None:
            self._sink = sink

        def post(self, url: str, **kwargs: object) -> _OkResponse:
            self._sink.append((url, cast(dict, kwargs)))
            return _OkResponse()

    client = ReportingClient(
        enabled=False,
        base_url="http://127.0.0.1:58473",
        token="",
    )
    cast(Any, client).session = _FakeSession(calls)

    client.run_start({"run_id": "example"})
    client.test_result({"run_id": "example", "status": "passed"})
    client.run_finish({"run_id": "example"})

    assert calls == []


def test_reporting_client_calls_api_when_enabled() -> None:
    calls: list[tuple[str, dict]] = []

    class _FakeSession:
        def __init__(self, sink: list[tuple[str, dict]]) -> None:
            self._sink = sink

        def post(self, url: str, **kwargs: object) -> _OkResponse:
            self._sink.append((url, cast(dict, kwargs)))
            return _OkResponse()

    client = ReportingClient(
        enabled=True,
        base_url="http://127.0.0.1:58473",
        token="",
    )
    cast(Any, client).session = _FakeSession(calls)

    payload = {"run_id": "example", "status": "passed"}
    client.test_result(payload)

    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:58473/test-run/test-result"


def test_load_env_reads_reporting_enabled_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPORTING_ENABLED", "0")
    env = load_env()
    assert env.reporting_enabled is False

    monkeypatch.setenv("REPORTING_ENABLED", "1")
    env = load_env()
    assert env.reporting_enabled is True


def test_load_env_reads_reporting_api_log_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPORTING_API_LOG_ENDPOINT", "/custom/log-endpoint")
    monkeypatch.setenv("REPORTING_API_LOG_LEVEL", "ERROR")
    env = load_env()
    assert env.reporting_api_log_endpoint == "/custom/log-endpoint"
    assert env.reporting_api_log_level == "ERROR"


def test_reporting_client_uploads_screenshots_for_artifacts_list_payload(tmp_path: Path) -> None:
    calls: list[tuple[str, dict]] = []

    class _FakeSession:
        def __init__(self, sink: list[tuple[str, dict]]) -> None:
            self._sink = sink

        def post(self, url: str, **kwargs: object) -> _OkResponse:
            self._sink.append((url, cast(dict, kwargs)))
            return _OkResponse()

    raw_path = tmp_path / "raw.png"
    ann_path = tmp_path / "annotated.png"
    raw_path.write_bytes(b"raw")
    ann_path.write_bytes(b"ann")

    client = ReportingClient(
        enabled=True,
        base_url="http://127.0.0.1:58473",
        token="",
    )
    cast(Any, client).session = _FakeSession(calls)

    payload = {
        "run_id": "example",
        "status": "failed",
        "artifacts": [
            {"kind": "screenshot_raw", "path": str(raw_path)},
            {"kind": "screenshot_annotated", "path": str(ann_path)},
        ],
    }

    client.test_result(payload)

    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:58473/test-run/test-result"
    request_kwargs = calls[0][1]
    assert "files" in request_kwargs
    assert "data" in request_kwargs
    assert "payload" in cast(dict, request_kwargs["data"])
    files = request_kwargs["files"]
    assert isinstance(files, list)
    assert len(files) == 2


def test_reporting_client_log_event_respects_level_threshold() -> None:
    calls: list[tuple[str, dict]] = []

    class _FakeSession:
        def __init__(self, sink: list[tuple[str, dict]]) -> None:
            self._sink = sink

        def post(self, url: str, **kwargs: object) -> _OkResponse:
            self._sink.append((url, cast(dict, kwargs)))
            return _OkResponse()

    client = ReportingClient(
        enabled=True,
        base_url="http://127.0.0.1:58473",
        token="",
        log_endpoint="/test-run/log",
        log_level="WARNING",
    )
    cast(Any, client).session = _FakeSession(calls)

    ignored = client.log_event(
        level="INFO",
        message="this should be ignored",
        run_id="example",
        nodeid="qa/test.py::test_case",
    )
    sent = client.log_event(
        level="ERROR",
        message="this should be sent",
        run_id="example",
        nodeid="qa/test.py::test_case",
    )

    assert ignored is False
    assert sent is True
    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:58473/test-run/log"


def test_reporting_client_async_flush_sends_events() -> None:
    calls: list[tuple[str, dict]] = []

    class _FakeSession:
        def __init__(self, sink: list[tuple[str, dict]]) -> None:
            self._sink = sink

        def post(self, url: str, **kwargs: object) -> _OkResponse:
            self._sink.append((url, cast(dict, kwargs)))
            return _OkResponse()

    client = ReportingClient(
        enabled=True,
        base_url="http://127.0.0.1:58473",
        token="",
        retries=0,
        async_enabled=True,
        async_queue_maxsize=20,
        async_max_attempts=2,
        async_max_retry_age_seconds=5,
        async_flush_timeout_seconds=2,
    )
    cast(Any, client).session = _FakeSession(calls)

    client.run_start({"run_id": "example"})
    client.test_result({"run_id": "example", "status": "passed", "test_id": "a"})
    client.run_finish({"run_id": "example"})

    assert client.flush(2) is True
    client.shutdown(2)
    urls = [url for url, _ in calls]
    assert "http://127.0.0.1:58473/test-run/start" in urls
    assert "http://127.0.0.1:58473/test-run/test-result" in urls
    assert "http://127.0.0.1:58473/test-run/finish" in urls


def test_reporting_client_async_retries_failed_event() -> None:
    calls: list[tuple[str, dict]] = []

    class _FlakySession:
        def __init__(self, sink: list[tuple[str, dict]]) -> None:
            self._sink = sink
            self._attempt = 0

        def post(self, url: str, **kwargs: object) -> _OkResponse:
            self._attempt += 1
            self._sink.append((url, cast(dict, kwargs)))
            if self._attempt == 1:
                raise requests.RequestException("temporary")
            return _OkResponse()

    client = ReportingClient(
        enabled=True,
        base_url="http://127.0.0.1:58473",
        token="",
        retries=0,
        async_enabled=True,
        async_queue_maxsize=20,
        async_max_attempts=3,
        async_max_retry_age_seconds=10,
        async_flush_timeout_seconds=3,
    )
    cast(Any, client).session = _FlakySession(calls)

    client.test_result({"run_id": "example", "status": "passed", "test_id": "retry-case"})

    deadline = time.time() + 4
    while time.time() < deadline:
        if len(calls) >= 2:
            break
        time.sleep(0.05)

    assert client.flush(3) is True
    client.shutdown(2)
    assert len(calls) >= 2
