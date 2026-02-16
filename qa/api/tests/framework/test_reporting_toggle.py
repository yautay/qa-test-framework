from __future__ import annotations

import pytest

from framework.env import load_env
from framework.reporting_client import ReportingClient

pytestmark = [pytest.mark.aso]


class _OkResponse:
    ok = True
    status_code = 200


def test_reporting_client_skips_calls_when_disabled(monkeypatch):
    calls: list[tuple[str, dict]] = []

    def _fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return _OkResponse()

    monkeypatch.setattr("framework.reporting_client.requests.post", _fake_post)

    client = ReportingClient(
        enabled=False,
        base_url="http://127.0.0.1:58473",
        token="",
    )

    client.run_start({"run_id": "example"})
    client.test_result({"run_id": "example", "status": "passed"})
    client.run_finish({"run_id": "example"})

    assert calls == []


def test_reporting_client_calls_api_when_enabled(monkeypatch):
    calls: list[tuple[str, dict]] = []

    def _fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return _OkResponse()

    monkeypatch.setattr("framework.reporting_client.requests.post", _fake_post)

    client = ReportingClient(
        enabled=True,
        base_url="http://127.0.0.1:58473",
        token="",
    )

    payload = {"run_id": "example", "status": "passed"}
    client.test_result(payload)

    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:58473/test-run/test-result"


def test_load_env_reads_reporting_enabled_from_environment(monkeypatch):
    monkeypatch.setenv("REPORTING_ENABLED", "0")
    env = load_env()
    assert env.reporting_enabled is False

    monkeypatch.setenv("REPORTING_ENABLED", "1")
    env = load_env()
    assert env.reporting_enabled is True
