from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

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
