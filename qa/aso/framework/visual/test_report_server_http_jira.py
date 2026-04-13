from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from framework.integrations.jira import JiraClientError
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
    def __init__(
        self,
        *,
        subtask_error: JiraClientError | None = None,
        existing_subtask_summaries: list[str] | None = None,
        create_issue_errors: list[JiraClientError] | None = None,
    ) -> None:
        self.comments: list[tuple[str, str]] = []
        self.attachments: list[tuple[str, str]] = []
        self.subtasks: list[tuple[str, str, str]] = []
        self.created_issues: list[dict[str, Any]] = []
        self._subtask_error = subtask_error
        self._existing_subtask_summaries = list(existing_subtask_summaries or [])
        self._create_issue_errors = list(create_issue_errors or [])
        self._create_meta_fields: dict[str, Any] = {
            "parent": {},
            "project": {},
            "summary": {},
            "issuetype": {},
            "description": {},
            "customfield_10010": {},
        }

    def add_comment(self, issue_key: str, body: str) -> dict[str, Any]:
        self.comments.append((issue_key, body))
        return {"id": issue_key}

    def add_attachment(self, issue_key: str, file_path: Path) -> dict[str, Any]:
        if not file_path.is_file():
            raise JiraClientError(f"attachment missing: {file_path}")
        self.attachments.append((issue_key, str(file_path)))
        return {"status": "ok"}

    def create_subtask(self, parent_issue_key: str, summary: str, description: str) -> dict[str, Any]:
        if self._subtask_error is not None:
            raise self._subtask_error
        self.subtasks.append((parent_issue_key, summary, description))
        self._existing_subtask_summaries.append(summary)
        return {"key": "ABC-200"}

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        if self._subtask_error is not None:
            raise self._subtask_error
        if self._create_issue_errors:
            raise self._create_issue_errors.pop(0)
        payload = dict(fields or {})
        self.created_issues.append(payload)
        parent = payload.get("parent") if isinstance(payload.get("parent"), dict) else {}
        parent_issue_key = str(parent.get("key", "ABC-1") or "ABC-1")
        summary = str(payload.get("summary", "") or "")
        description = str(payload.get("description", "") or "")
        self.subtasks.append((parent_issue_key, summary, description))
        self._existing_subtask_summaries.append(summary)
        return {"key": "ABC-200"}

    def list_subtasks(self, parent_issue_key: str) -> list[dict[str, Any]]:
        return [
            {"key": f"{parent_issue_key}-{idx + 1}", "summary": summary}
            for idx, summary in enumerate(self._existing_subtask_summaries)
        ]

    def get_issue_details(self, issue_key: str, *, fields: str = "*all") -> dict[str, Any]:
        return {
            "id": "10001",
            "key": issue_key,
            "fields": {
                "project": {"key": "ABC"},
                "customfield_10010": "inherited-value",
            },
        }

    def get_create_meta_fields(self, project_key: str, issue_type_name: str = "Sub-task") -> dict[str, Any] | None:
        return dict(self._create_meta_fields)


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


def _build_context(
    repo_root: Path,
    report_dir: Path,
    jira_client: _FakeJiraClient,
    *,
    framework_mode: str = "local",
) -> ReportServerContext:
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
        framework_mode=framework_mode,
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


def test_jira_comment_mode_subtask_creates_subtask_and_uploads_attachment(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    fake_client = _FakeJiraClient()
    context = _build_context(repo_root, report_dir, fake_client)
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note", "mode": "subtask"},
            headers={"Host": "localhost"},
        )
        assert status == 200
        assert payload["accepted"] is True
        assert payload["mode"] == "subtask"
        assert payload["issue"] == "ABC-200"
        assert len(fake_client.subtasks) == 1
        assert fake_client.subtasks[0][1].startswith("[bug] VRT #1 - ")
        assert not fake_client.comments
        assert fake_client.attachments[0][0] == "ABC-200"
    finally:
        _stop_server(server, thread)


def test_jira_comment_mode_subtask_increments_existing_counter(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    fake_client = _FakeJiraClient(
        existing_subtask_summaries=["[bug] VRT #1 - 01/04/2026 09:10", "[bug] VRT #4 - 01/04/2026 11:11"]
    )
    context = _build_context(repo_root, report_dir, fake_client)
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note", "mode": "subtask"},
            headers={"Host": "localhost"},
        )
        assert status == 200
        assert payload["accepted"] is True
        assert payload["mode"] == "subtask"
        assert fake_client.subtasks[0][1].startswith("[bug] VRT #5 - ")
    finally:
        _stop_server(server, thread)


def test_jira_comment_mode_auto_falls_back_to_comment_when_subtask_fails(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    fake_client = _FakeJiraClient(subtask_error=JiraClientError("cannot create sub-task", status=400))
    context = _build_context(repo_root, report_dir, fake_client)
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note", "mode": "auto"},
            headers={"Host": "localhost"},
        )
        assert status == 200
        assert payload["accepted"] is True
        assert payload["mode"] == "comment"
        assert payload["requested_mode"] == "auto"
        assert fake_client.comments[0][0] == "ABC-1"
        assert fake_client.attachments[0][0] == "ABC-1"
    finally:
        _stop_server(server, thread)


def test_jira_comment_mode_subtask_retries_with_required_parent_fields(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    fake_client = _FakeJiraClient(
        create_issue_errors=[
            JiraClientError(
                "status=400 body=required field",
                status=400,
                payload={"errors": {"customfield_10010": "Field is required"}},
            )
        ]
    )
    context = _build_context(repo_root, report_dir, fake_client)
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note", "mode": "subtask"},
            headers={"Host": "localhost"},
        )
        assert status == 200
        assert payload["accepted"] is True
        assert payload["mode"] == "subtask"
        assert fake_client.created_issues
        last_fields = fake_client.created_issues[-1]
        assert last_fields.get("customfield_10010") == "inherited-value"
    finally:
        _stop_server(server, thread)


def test_jira_comment_server_mode_keeps_diff_url_and_skips_attachments(tmp_path: Path) -> None:
    repo_root, report_dir, _ = _prepare_report(tmp_path, "run-jira")
    fake_client = _FakeJiraClient()
    context = _build_context(repo_root, report_dir, fake_client, framework_mode="server")
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note", "mode": "comment"},
            headers={"Host": "localhost"},
        )
        assert status == 200
        assert payload["accepted"] is True
        assert payload["framework_mode"] == "server"
        assert payload["attachments"] == 0
        body = fake_client.comments[0][1]
        assert "[diff|http://localhost/reports/run-jira/diff/case-1.png]" in body
        assert "thumbnail" not in body
        assert len(fake_client.attachments) == 0
    finally:
        _stop_server(server, thread)


def test_jira_comment_includes_execution_target_full_url_in_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    run_id = "run-jira"
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
                        "test_metadata": {
                            "scenario": {
                                "target_url": "/produkt/lodz",
                            },
                            "execution": {
                                "target_base_url": "https://shop.example.com",
                                "browser_version": "123.0.1",
                            },
                            "run": {
                                "target_git_info": {
                                    "frontend": {"branch": "feature/front", "commit": "abc1234"},
                                    "backend": {"branch": "feature/back", "commit": "def5678"},
                                }
                            },
                        },
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

    fake_client = _FakeJiraClient()
    context = _build_context(repo_root, report_dir, fake_client)
    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(
            base_url,
            "/api/reports/run-jira/jira/comment",
            method="POST",
            body={"jira_ticket": "ABC-1", "user_note": "note", "mode": "comment"},
            headers={"Host": "localhost"},
        )
        assert status == 200
        assert payload["accepted"] is True
        body = fake_client.comments[0][1]
        assert "🟢" not in body
        assert "🔴 visual-regression: FAIL" in body
        assert "{panel:title=BUG SECTION" in body
        assert "*Backend Git:* branch=feature/back | commit=def5678" in body
        assert "*Frontend Git:* branch=feature/front | commit=abc1234" in body
        assert "browser.details: chromium | version=123.0.1" in body
        assert "execution.target_full_url: https://shop.example.com/produkt/lodz" in body
        assert "thumbnail" in body
    finally:
        _stop_server(server, thread)
