from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from framework.artifacts import build_run_artifacts
from framework.browser import BrowserSession
from framework.env import load_env
from qa.conftest import (
    _artifact_entry,
    _capture_target_git_info,
    _publish_report_metadata,
    _read_perceptual_quality_signals,
    _refresh_environment_probe_metadata,
    _resolve_execution_context,
    _write_test_steps_artifact,
)

try:
    from pytest_metadata.plugin import metadata_key as pytest_metadata_key
except Exception:  # pragma: no cover - optional dependency
    pytest_metadata_key = None

pytestmark = [pytest.mark.aso]


def test_artifact_entry_reads_real_file_stats(tmp_path: Path) -> None:
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"abc")

    payload = _artifact_entry("visual_actual", str(sample))

    assert payload["available"] is True
    assert payload["size_bytes"] == 3
    assert payload["size_mib"] == 0.0
    assert payload["sha256"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_artifact_entry_marks_missing_as_unavailable() -> None:
    payload = _artifact_entry("visual_heatmap", "")

    assert payload["available"] is False
    assert payload["size_bytes"] == 0
    assert payload["size_mib"] == 0.0
    assert payload["sha256"] == ""


def test_artifact_entry_failed_dom_with_real_html_file(tmp_path: Path) -> None:
    html_content = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body><h1>Failed Test DOM</h1><p>Content snapshot</p></body>
</html>"""
    html_file = tmp_path / "test_failed.html"
    html_file.write_text(html_content, encoding="utf-8")

    payload = _artifact_entry("failed_dom", str(html_file))

    assert payload["available"] is True
    assert payload["size_bytes"] == len(html_content.encode("utf-8"))
    assert payload["size_mib"] >= 0.0  # Small files can have 0.0 MiB
    assert payload["kind"] == "failed_dom"
    assert "sha256" in payload


def test_artifact_entry_failed_dom_missing_path() -> None:
    payload = _artifact_entry("failed_dom", "")

    assert payload["available"] is False
    assert payload["size_bytes"] == 0
    assert payload["size_mib"] == 0.0
    assert payload["sha256"] == ""
    assert payload["kind"] == "failed_dom"


def test_write_test_steps_artifact_creates_json_file(tmp_path: Path) -> None:
    run_artifacts = build_run_artifacts(str(tmp_path / "artifacts"), run_id="run-steps")
    config = SimpleNamespace(_run_artifacts=run_artifacts)

    artifact_path = _write_test_steps_artifact(
        config,
        nodeid="qa/e2e/sample.py::test_case[param]",
        status="failed",
        finished_at="2026-01-01T12:00:00+00:00",
        steps=[
            {
                "title": "Krok 1",
                "status": "passed",
                "duration_ms": 123,
            }
        ],
    )

    assert artifact_path
    payload = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    assert payload["nodeid"] == "qa/e2e/sample.py::test_case[param]"
    assert payload["status"] == "failed"
    assert payload["step_count"] == 1


def test_read_perceptual_quality_signals_uses_defaults_without_status_file(tmp_path: Path) -> None:
    payload = _read_perceptual_quality_signals(tmp_path)

    assert payload["pms_used"] is False
    assert payload["pms_jobs_submitted"] == 0
    assert payload["pms_jobs_done"] == 0
    assert payload["pms_jobs_error"] == 0
    assert payload["pms_jobs_skipped"] == 0
    assert payload["pms_unavailable_reason"] == ""


def test_read_perceptual_quality_signals_reads_status_payload(tmp_path: Path) -> None:
    status_path = tmp_path / "visual" / "perceptual-status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(
            {
                "submitted_count": 7,
                "done_count": 5,
                "error_count": 2,
                "skipped_count": 3,
                "used": True,
                "unavailable_reason": "",
            }
        ),
        encoding="utf-8",
    )

    payload = _read_perceptual_quality_signals(tmp_path)

    assert payload["pms_used"] is True
    assert payload["pms_jobs_submitted"] == 7
    assert payload["pms_jobs_done"] == 5
    assert payload["pms_jobs_error"] == 2
    assert payload["pms_jobs_skipped"] == 3


def test_resolve_execution_context_uses_connected_browser_session() -> None:
    env = load_env()
    session = BrowserSession(
        browser=object(),
        provider="selenium_cdp",
        endpoint="ws://10.0.0.10:9222/devtools/browser/abc",
        selenium_session_id="session-1",
        selenium_grid_url="http://10.0.0.10:4444",
    )

    payload = _resolve_execution_context(env, session)

    assert payload["grid_enabled"] is True
    assert payload["grid_provider"] == "selenium_cdp"
    assert payload["grid_endpoint"] == "http://10.0.0.10:4444"
    assert payload["grid_cdp_endpoint"] == "ws://10.0.0.10:9222/devtools/browser/abc"


def test_capture_target_git_info_returns_not_configured_when_no_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RUN_GIT_INFO_FRONTEND_ENDPOINT", raising=False)
    monkeypatch.delenv("RUN_GIT_INFO_BACKEND_ENDPOINT", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("BASE_URL_OVERRIDE", raising=False)
    env = load_env()

    payload = _capture_target_git_info(env)

    assert payload["frontend"]["status"] == "not_configured"
    assert payload["backend"]["status"] == "not_configured"


def test_capture_target_git_info_handles_invalid_payload_as_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        status_code = 200
        url = "https://example.test/git-info"

        @staticmethod
        def json() -> object:
            return {"branch": "feature/demo"}

    def _fake_get(*_args, **_kwargs):
        return _Response()

    monkeypatch.setattr("qa.conftest.requests.get", _fake_get)
    monkeypatch.setenv("BASE_URL", "https://example.test")
    monkeypatch.setenv("RUN_GIT_INFO_FRONTEND_ENDPOINT", "/git-info")
    monkeypatch.setenv("RUN_GIT_INFO_BACKEND_ENDPOINT", "/backend-git-info")
    env = load_env()

    payload = _capture_target_git_info(env)

    assert payload["frontend"]["status"] == "invalid_payload"
    assert payload["frontend"]["error"] == "missing_branch_or_commit"


def test_capture_target_git_info_accepts_commit_hash_camel_case(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        status_code = 200
        url = "https://example.test/git-info"
        headers: dict[str, str] = {}
        text = "{}"

        @staticmethod
        def json() -> object:
            return {"branch": "feature/demo", "commitHash": "abc1234"}

    def _fake_get(*_args, **_kwargs):
        return _Response()

    monkeypatch.setattr("qa.conftest.requests.get", _fake_get)
    monkeypatch.setenv("BASE_URL", "https://example.test")
    monkeypatch.setenv("RUN_GIT_INFO_FRONTEND_ENDPOINT", "/git-info")
    monkeypatch.setenv("RUN_GIT_INFO_BACKEND_ENDPOINT", "/git-info")
    env = load_env()

    payload = _capture_target_git_info(env)

    assert payload["frontend"]["status"] == "ok"
    assert payload["frontend"]["branch"] == "feature/demo"
    assert payload["frontend"]["commit"] == "abc1234"


def test_refresh_environment_probe_updates_target_git_info_from_resolved_base_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class _Response:
        status_code = 200
        url = "https://komputronik-kokoko.gamma.netcorner.pl/git-info"
        headers: dict[str, str] = {}
        text = "{}"

        @staticmethod
        def json() -> object:
            return {"branch": "feature/demo", "commit": "abc1234"}

    def _fake_get(url: str, **_kwargs):
        if url.rstrip("/") == "https://komputronik-kokoko.gamma.netcorner.pl":
            return _Response()
        if url.endswith("/git-info"):
            return _Response()
        raise RuntimeError(f"unexpected url: {url}")

    monkeypatch.setattr("qa.conftest.requests.get", _fake_get)
    monkeypatch.setattr(
        "qa.conftest._resolve_probe_base_url_from_items",
        lambda _config, _items: ("https://komputronik-kokoko.gamma.netcorner.pl", "target_mapping"),
    )
    env = replace(
        load_env(),
        base_url="",
        server_name="kokoko.gamma",
        run_git_info_frontend_endpoint="/git-info",
        run_git_info_backend_endpoint="/git-info",
    )

    metadata = {
        "tester": "",
        "run_note": "",
        "target_git_info": {
            "frontend": {"status": "not_configured"},
            "backend": {"status": "not_configured"},
        },
        "environment_probe": {
            "request_url": "",
        },
    }
    config = SimpleNamespace(
        _runtime_env=env,
        _run_metadata=metadata,
        _environment_probe_resolved=False,
        _target_git_info_warned_events=set(),
        _run_artifacts=None,
    )
    item = SimpleNamespace(nodeid="qa/e2e/netcorner/nuxt/pl/tests/test_dummy.py::test_case")

    _refresh_environment_probe_metadata(config, [cast(pytest.Item, item)])

    refreshed_metadata = cast(dict[str, Any], config._run_metadata)
    assert refreshed_metadata["target_git_info"]["frontend"]["status"] == "ok"
    assert refreshed_metadata["target_git_info"]["frontend"]["branch"] == "feature/demo"
    assert refreshed_metadata["target_git_info"]["frontend"]["commit"] == "abc1234"


def test_publish_report_metadata_writes_allure_environment_properties(tmp_path: Path) -> None:
    allure_dir = tmp_path / "allure-results"
    config = SimpleNamespace(
        option=SimpleNamespace(allure_report_dir=str(allure_dir)),
        getoption=lambda _name: str(allure_dir),
        stash={},
    )

    _publish_report_metadata(
        config,
        {
            "tester": "qa-user",
            "run_note": "nightly",
            "target_git_info": {
                "frontend": {
                    "branch": "feature/demo-ui",
                    "commit": "abc1234",
                    "status": "ok",
                },
                "backend": {
                    "branch": "feature/demo-api",
                    "commit": "def5678",
                    "status": "ok",
                },
            },
        },
    )

    environment_path = allure_dir / "environment.properties"
    assert environment_path.is_file()
    content = environment_path.read_text(encoding="utf-8")
    assert "target_git_frontend=feature/demo-ui @ abc1234" in content
    assert "target_git_backend=feature/demo-api @ def5678" in content
    assert "target_git_frontend_status=ok" in content


def test_publish_report_metadata_updates_pytest_html_metadata_stash() -> None:
    if pytest_metadata_key is None:
        pytest.skip("pytest-metadata plugin unavailable")

    config = SimpleNamespace(
        option=SimpleNamespace(allure_report_dir=""),
        stash={},
    )

    _publish_report_metadata(
        config,
        {
            "tester": "qa-user",
            "run_note": "nightly",
            "target_git_info": {
                "frontend": {
                    "branch": "feature/demo-ui",
                    "commit": "abc1234",
                    "status": "ok",
                },
                "backend": {
                    "status": "not_configured",
                },
            },
        },
    )

    payload = config.stash[pytest_metadata_key]
    assert payload["tester"] == "qa-user"
    assert payload["run_note"] == "nightly"
    assert payload["target_git_frontend_branch"] == "feature/demo-ui"
    assert payload["target_git_frontend_commit"] == "abc1234"
    assert payload["target_git_backend_status"] == "not_configured"
