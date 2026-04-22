from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

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

    called: dict[str, int] = {"save": 0, "load": 0, "detect": 0}

    def _mark_load(*_args, **_kwargs) -> dict[str, float]:
        called["load"] += 1
        return {}

    def _mark_detect(*_args, **_kwargs) -> list[object]:
        called["detect"] += 1
        return []

    monkeypatch.setattr(
        runtime_conftest,
        "save_run_timings",
        lambda *_args, **_kwargs: called.__setitem__("save", called["save"] + 1),
    )
    monkeypatch.setattr(
        runtime_conftest,
        "load_previous_timings",
        _mark_load,
    )
    monkeypatch.setattr(
        runtime_conftest,
        "detect_slow_regressions",
        _mark_detect,
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

    assert called == {"save": 0, "load": 0, "detect": 0}
    assert not (run_artifacts.logs / "test_durations.json").exists()
    assert client.run_finish_calls
    metadata = cast(dict[str, Any], client.run_finish_calls[0]["metadata"])
    assert metadata["target_git_info"]["frontend"]["status"] == "not_configured"
    assert metadata["target_git_info"]["backend"]["status"] == "not_configured"
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


def test_pytest_sessionfinish_run_finish_prefers_target_git_info_from_run_metadata_file(tmp_path: Path) -> None:
    run_artifacts = build_run_artifacts(str(tmp_path / "artifacts"), run_id="run-finish-metadata")
    metadata_path = run_artifacts.root / "run-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "tester": "qa-user",
                "run_note": "nightly",
                "target_git_info": {
                    "frontend": {
                        "branch": "feature/demo-ui",
                        "commit": "abc1234",
                        "endpoint": "/git-info",
                        "url": "https://example.test/git-info",
                        "status": "ok",
                        "error": "",
                        "fetched_at_utc": "2026-01-01T00:00:00Z",
                    },
                    "backend": {
                        "branch": "feature/demo-api",
                        "commit": "def5678",
                        "endpoint": "/git-info",
                        "url": "https://example.test/api/git-info",
                        "status": "ok",
                        "error": "",
                        "fetched_at_utc": "2026-01-01T00:00:00Z",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    class _Client:
        def __init__(self) -> None:
            self.run_finish_calls: list[dict[str, object]] = []

        def run_finish(self, payload: dict[str, object]) -> None:
            self.run_finish_calls.append(payload)

        def flush(self, timeout_seconds: int) -> None:
            _ = timeout_seconds

        def shutdown(self, timeout_seconds: int) -> None:
            _ = timeout_seconds

    client = _Client()

    config = SimpleNamespace(
        _run_artifacts=run_artifacts,
        _run_uid="uid-3",
        _test_case_timings={},
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

    assert client.run_finish_calls
    metadata = cast(dict[str, Any], client.run_finish_calls[0]["metadata"])
    assert metadata["target_git_info"]["frontend"]["branch"] == "feature/demo-ui"
    assert metadata["target_git_info"]["frontend"]["commit"] == "abc1234"
    assert metadata["target_git_info"]["backend"]["branch"] == "feature/demo-api"
    assert metadata["target_git_info"]["backend"]["commit"] == "def5678"
