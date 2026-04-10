from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from framework.reporting.report_server.context import ReportServerContext
from framework.visual.baseline_store import BaselineStore
from qa.aso.framework.visual.report_server_http_test_helpers import (
    _env,
    _http_json,
    _start_server,
    _stop_server,
)


pytestmark = [pytest.mark.aso]


class _FakeJiraClient:
    def __init__(self) -> None:
        self.comments: list[tuple[str, str]] = []
        self.attachments: list[tuple[str, str]] = []

    def add_comment(self, issue_key: str, body: str) -> dict[str, Any]:
        self.comments.append((issue_key, body))
        return {"id": issue_key}

    def add_attachment(self, issue_key: str, file_path: Path) -> dict[str, Any]:
        self.attachments.append((issue_key, str(file_path)))
        return {"status": "ok"}


def _prepare_report(tmp_path: Path, run_id: str) -> tuple[Path, Path, Path]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    report_dir = repo_root / "artifacts" / run_id / "visual"
    report_dir.mkdir(parents=True)
    (report_dir / ".report-ready.json").write_text('{"ready": true}\n', encoding="utf-8")
    (report_dir / "results.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario_id": "case-1",
                        "status": "failed",
                        "suite_id": "suite-1",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "actual_path": "actual/case-1.png",
                        "diff_path": "diff/case-1.png",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    diff_dir = report_dir / "diff"
    diff_dir.mkdir(parents=True)
    (diff_dir / "case-1.png").write_bytes(b"diff")
    state = {
        "test_cases": {
            "case-1::actual/case-1.png::::diff/case-1.png": {
                "bug": {"locked": True, "synced": False, "note": "bug"},
                "aso": {"locked": False, "synced": False, "note": ""},
            }
        },
        "outbox": [],
    }
    (report_dir.parent / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return repo_root, report_dir, repo_root / "ui-dist"


def _build_context(repo_root: Path, report_dir: Path, jira_client: _FakeJiraClient) -> ReportServerContext:
    ui_dist = repo_root / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html></html>", encoding="utf-8")
    return ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(_env(), repo_root),
        run_dirs={"run-jira": report_dir},
        jira_enabled=True,
        jira_url="https://jira.example",
        jira_verify_ssl=True,
        jira_auth_mode="basic",
        jira_auth_configured=True,
        jira_client=jira_client,
        jira_retry_max=1,
        jira_upload_delay_seconds=0,
        jira_pixel_diff_max_width_px=320,
    )


def test_jira_comment_requires_valid_ticket(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    context = _build_context(repo_root, report_dir, _FakeJiraClient())
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "invalid", "user_note": "note"},
        )
        assert status == 400
        assert payload["error"].startswith("invalid jira_ticket")
    finally:
        _stop_server(server, thread)


def test_jira_comment_requires_auth_when_not_configured(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    context = _build_context(repo_root, report_dir, _FakeJiraClient())
    context.jira_auth_configured = False
    context.jira_client = None
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note"},
        )
        assert status == 400
        assert payload["error"].startswith("auth credentials required")
    finally:
        _stop_server(server, thread)


def test_jira_comment_success_uploads_comment_and_attachment(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    fake_client = _FakeJiraClient()
    context = _build_context(repo_root, report_dir, fake_client)
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note"},
            headers={"Host": "localhost"},
        )
        assert status == 200
        assert payload["accepted"] is True
        assert fake_client.comments[0][0] == "ABC-1"
        assert len(fake_client.attachments) == 1
    finally:
        _stop_server(server, thread)
