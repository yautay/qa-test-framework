from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework.browser import BrowserSession
from qa.conftest import _artifact_entry, _read_perceptual_quality_signals
from framework.env import load_env
from qa.conftest import _resolve_execution_context
from qa.conftest import _capture_target_git_info

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
    monkeypatch.delenv("RUN_GIT_INFO_FRONTEND_URL", raising=False)
    monkeypatch.delenv("RUN_GIT_INFO_BACKEND_URL", raising=False)
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
    monkeypatch.setenv("RUN_GIT_INFO_FRONTEND_URL", "https://example.test/git-info")
    monkeypatch.delenv("RUN_GIT_INFO_BACKEND_URL", raising=False)
    env = load_env()

    payload = _capture_target_git_info(env)

    assert payload["frontend"]["status"] == "invalid_payload"
    assert payload["frontend"]["error"] == "missing_branch_or_commit"
