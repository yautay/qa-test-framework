from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from framework.artifacts import build_run_artifacts
from framework.env import load_env
from qa import conftest as runtime_conftest

pytestmark = [pytest.mark.aso]


def test_pytest_sessionfinish_collect_only_skips_timing_snapshots_and_regressions(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_artifacts = build_run_artifacts(str(tmp_path / "artifacts"), run_id="run-collect-only")

    class _Client:
        def __init__(self) -> None:
            self.run_finish_calls: list[dict[str, object]] = []
            self.flush_calls: list[int] = []
            self.shutdown_calls: list[int] = []

        def run_finish(self, payload: dict[str, object]) -> None:
            self.run_finish_calls.append(payload)

        def flush(self, timeout_seconds: int) -> None:
            self.flush_calls.append(int(timeout_seconds))

        def shutdown(self, timeout_seconds: int) -> None:
            self.shutdown_calls.append(int(timeout_seconds))

    client = _Client()

    called: dict[str, int] = {"save": 0, "load": 0, "detect": 0, "warn": 0}
    monkeypatch.setattr(
        runtime_conftest, "save_run_timings", lambda *_args, **_kwargs: called.__setitem__("save", called["save"] + 1)
    )
    monkeypatch.setattr(
        runtime_conftest,
        "load_previous_timings",
        lambda *_args, **_kwargs: called.__setitem__("load", called["load"] + 1) or {},
    )
    monkeypatch.setattr(
        runtime_conftest,
        "detect_slow_regressions",
        lambda *_args, **_kwargs: called.__setitem__("detect", called["detect"] + 1) or [],
    )
    monkeypatch.setattr(
        runtime_conftest.logger,
        "warning",
        lambda *_args, **_kwargs: called.__setitem__("warn", called["warn"] + 1),
    )

    config = SimpleNamespace(
        _run_artifacts=run_artifacts,
        _run_uid="uid-1",
        _test_case_timings={"qa/test.py::test_case": 1.234},
        option=SimpleNamespace(collectonly=True),
        _runtime_env=load_env(),
        _run_metadata={"tester": "", "run_note": ""},
        _result_counters={
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
            "error": 0,
        },
        _session_started=time.time() - 0.2,
        _reporting_suspended=False,
        _reporting_client=client,
    )
    session = SimpleNamespace(config=config)

    runtime_conftest.pytest_sessionfinish(session, 0)

    assert called == {"save": 0, "load": 0, "detect": 0, "warn": 0}
    assert not (run_artifacts.logs / "test_durations.json").exists()
    assert client.run_finish_calls
    assert client.flush_calls
    assert client.shutdown_calls


def test_pytest_sessionfinish_controller_falls_back_to_local_timings_when_no_worker_files(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_artifacts = build_run_artifacts(str(tmp_path / "artifacts"), run_id="run-controller-fallback")

    class _Client:
        def run_finish(self, _payload: dict[str, object]) -> None:
            return

        def flush(self, timeout_seconds: int) -> None:
            _ = timeout_seconds

        def shutdown(self, timeout_seconds: int) -> None:
            _ = timeout_seconds

    class _PluginManager:
        @staticmethod
        def hasplugin(name: str) -> bool:
            return name == "xdist"

    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)

    config = SimpleNamespace(
        _run_artifacts=run_artifacts,
        _run_uid="uid-2",
        _test_case_timings={"qa/test.py::test_case": 1.234},
        option=SimpleNamespace(collectonly=False),
        pluginmanager=_PluginManager(),
        _runtime_env=load_env(),
        _run_metadata={"tester": "", "run_note": ""},
        _result_counters={
            "total": 1,
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
            "error": 0,
        },
        _session_started=time.time() - 0.2,
        _reporting_suspended=False,
        _reporting_client=_Client(),
    )
    session = SimpleNamespace(config=config)

    runtime_conftest.pytest_sessionfinish(session, 0)

    payload = (run_artifacts.logs / "test_durations.json").read_text(encoding="utf-8")
    assert "qa/test.py::test_case" in payload
