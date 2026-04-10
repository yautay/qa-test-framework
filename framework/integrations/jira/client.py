from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from loguru import logger


@dataclass(frozen=True)
class JiraAuth:
    mode: str  # "basic" | "token"
    username: str
    password: str
    api_token: str


class JiraClientError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class JiraClient:
    def __init__(
        self,
        *,
        base_url: str,
        verify_ssl: bool,
        auth: JiraAuth | None,
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = str(base_url or "").rstrip("/")
        self.verify_ssl = bool(verify_ssl)
        self.auth = auth
        self.timeout_seconds = max(5, int(timeout_seconds))
        self._session = requests.Session()

    def _auth_header(self) -> dict[str, str]:
        if not self.auth:
            return {}
        username = str(self.auth.username or "").strip()
        if not username:
            return {}
        if self.auth.mode == "token":
            secret = str(self.auth.api_token or "").strip()
        else:
            secret = str(self.auth.password or "").strip()
        if not secret:
            return {}
        raw = f"{username}:{secret}"
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        try:
            response = self._session.request(
                method=method,
                url=url,
                timeout=self.timeout_seconds,
                verify=self.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            logger.opt(exception=True).warning("jira_request_failed", url=url, method=method)
            raise JiraClientError(str(exc)) from exc
        if not response.ok:
            message = response.text[:400]
            logger.warning("jira_request_non_ok", url=url, method=method, status=response.status_code)
            raise JiraClientError(f"status={response.status_code} body={message}", status=response.status_code)
        return response

    def add_comment(self, issue_key: str, body: str) -> dict[str, Any]:
        if not self.base_url:
            raise JiraClientError("Jira base URL is not configured")
        if not issue_key:
            raise JiraClientError("issue key is required for Jira comment")
        url = f"{self.base_url}/rest/api/2/issue/{issue_key.strip()}/comment"
        headers = {"Accept": "application/json"}
        headers.update(self._auth_header())
        headers["Content-Type"] = "application/json"
        payload = {"body": body}
        response = self._request("POST", url, json=payload, headers=headers)
        try:
            return response.json()
        except ValueError:
            return {"status": "ok"}

    def add_attachment(self, issue_key: str, file_path: Path) -> dict[str, Any]:
        if not self.base_url:
            raise JiraClientError("Jira base URL is not configured")
        if not issue_key:
            raise JiraClientError("issue key is required for Jira attachment")
        if not file_path.is_file():
            raise JiraClientError(f"attachment missing: {file_path}")
        url = f"{self.base_url}/rest/api/2/issue/{issue_key.strip()}/attachments"
        headers = {"Accept": "application/json", "X-Atlassian-Token": "no-check"}
        headers.update(self._auth_header())
        with file_path.open("rb") as fd:
            files = {"file": (file_path.name, fd, "application/octet-stream")}
            response = self._request("POST", url, files=files, headers=headers)
        try:
            return response.json()
        except ValueError:
            return {"status": "ok"}

    def create_subtask(self, parent_issue_key: str, summary: str, description: str) -> dict[str, Any]:
        if not self.base_url:
            raise JiraClientError("Jira base URL is not configured")
        parent = str(parent_issue_key or "").strip()
        if not parent:
            raise JiraClientError("parent issue key is required for Jira sub-task")
        title = str(summary or "").strip()
        if not title:
            raise JiraClientError("sub-task summary is required")
        url = f"{self.base_url}/rest/api/2/issue"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        headers.update(self._auth_header())
        payload = {
            "fields": {
                "parent": {"key": parent},
                "summary": title,
                "issuetype": {"name": "Sub-task"},
                "description": str(description or ""),
            }
        }
        response = self._request("POST", url, json=payload, headers=headers)
        try:
            data = response.json()
        except ValueError:
            return {"status": "ok"}
        if not isinstance(data, dict):
            return {"status": "ok"}
        return data

    def list_subtasks(self, parent_issue_key: str) -> list[dict[str, Any]]:
        if not self.base_url:
            raise JiraClientError("Jira base URL is not configured")
        parent = str(parent_issue_key or "").strip()
        if not parent:
            raise JiraClientError("parent issue key is required for listing Jira sub-tasks")
        url = f"{self.base_url}/rest/api/2/issue/{parent}?fields=subtasks"
        headers = {"Accept": "application/json"}
        headers.update(self._auth_header())
        response = self._request("GET", url, headers=headers)
        try:
            payload = response.json()
        except ValueError:
            return []
        if not isinstance(payload, dict):
            return []
        fields = payload.get("fields")
        if not isinstance(fields, dict):
            return []
        raw_subtasks = fields.get("subtasks")
        if not isinstance(raw_subtasks, list):
            return []
        out: list[dict[str, Any]] = []
        for item in raw_subtasks:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "") or "").strip()
            details = item.get("fields") if isinstance(item.get("fields"), dict) else {}
            summary = str(details.get("summary", "") or "")
            out.append({"key": key, "summary": summary})
        return out
