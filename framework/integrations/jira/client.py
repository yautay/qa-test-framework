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
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        payload: Any | None = None,
        status_text: str = "",
    ) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload
        self.status_text = status_text


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
            payload = self._parse_response_payload(response)
            message = self._payload_to_text(payload) or response.text[:400]
            logger.warning("jira_request_non_ok", url=url, method=method, status=response.status_code)
            raise JiraClientError(
                f"status={response.status_code} body={message}",
                status=response.status_code,
                payload=payload,
                status_text=str(response.reason or ""),
            )
        return response

    @staticmethod
    def _parse_response_payload(response: requests.Response) -> Any:
        text = str(getattr(response, "text", "") or "").strip()
        if not text:
            return {}
        try:
            return response.json()
        except ValueError:
            return {"raw": text[:4000]}

    @staticmethod
    def _payload_to_text(payload: Any) -> str:
        if payload is None:
            return ""
        if isinstance(payload, str):
            return payload.strip()
        if not isinstance(payload, dict):
            return str(payload).strip()
        parts: list[str] = []
        error_messages = payload.get("errorMessages")
        if isinstance(error_messages, list):
            entries = [str(item).strip() for item in error_messages if str(item).strip()]
            if entries:
                parts.append("; ".join(entries))
        errors = payload.get("errors")
        if isinstance(errors, dict):
            for key, value in errors.items():
                token = str(value or "").strip()
                if token:
                    parts.append(f"{key}: {token}")
        raw = str(payload.get("raw", "") or "").strip()
        if raw:
            parts.append(raw)
        return " | ".join(parts).strip()

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

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        if not self.base_url:
            raise JiraClientError("Jira base URL is not configured")
        url = f"{self.base_url}/rest/api/2/issue"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        headers.update(self._auth_header())
        payload = {"fields": fields if isinstance(fields, dict) else {}}
        response = self._request("POST", url, json=payload, headers=headers)
        try:
            data = response.json()
        except ValueError:
            return {"status": "ok"}
        if not isinstance(data, dict):
            return {"status": "ok"}
        return data

    def create_subtask(self, parent_issue_key: str, summary: str, description: str) -> dict[str, Any]:
        parent = str(parent_issue_key or "").strip()
        if not parent:
            raise JiraClientError("parent issue key is required for Jira sub-task")
        title = str(summary or "").strip()
        if not title:
            raise JiraClientError("sub-task summary is required")
        fields = {
            "parent": {"key": parent},
            "summary": title,
            "issuetype": {"name": "Sub-task"},
            "description": str(description or ""),
        }
        return self.create_issue(fields)

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

    def get_issue_details(self, issue_key: str, *, fields: str = "*all") -> dict[str, Any]:
        if not self.base_url:
            raise JiraClientError("Jira base URL is not configured")
        key = str(issue_key or "").strip()
        if not key:
            raise JiraClientError("issue key is required for Jira issue details")
        request_fields = str(fields or "*all").strip() or "*all"
        url = f"{self.base_url}/rest/api/2/issue/{key}?fields={request_fields}"
        headers = {"Accept": "application/json"}
        headers.update(self._auth_header())
        response = self._request("GET", url, headers=headers)
        try:
            payload = response.json()
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def get_create_meta_fields(self, project_key: str, issue_type_name: str = "Sub-task") -> dict[str, Any] | None:
        if not self.base_url:
            raise JiraClientError("Jira base URL is not configured")
        project = str(project_key or "").strip()
        if not project:
            return None
        issue_type = str(issue_type_name or "Sub-task").strip() or "Sub-task"
        url = (
            f"{self.base_url}/rest/api/2/issue/createmeta"
            f"?projectKeys={project}&issuetypeNames={issue_type}&expand=projects.issuetypes.fields"
        )
        headers = {"Accept": "application/json"}
        headers.update(self._auth_header())
        try:
            response = self._request("GET", url, headers=headers)
        except JiraClientError as exc:
            if int(exc.status or 0) in {400, 403, 404}:
                return None
            raise
        try:
            payload = response.json()
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        projects = payload.get("projects") if isinstance(payload.get("projects"), list) else []
        if not projects:
            return None
        project_item = projects[0] if isinstance(projects[0], dict) else {}
        issue_types = project_item.get("issuetypes") if isinstance(project_item.get("issuetypes"), list) else []
        if not issue_types:
            return None
        issue_type_item = issue_types[0] if isinstance(issue_types[0], dict) else {}
        fields_payload = issue_type_item.get("fields") if isinstance(issue_type_item.get("fields"), dict) else None
        if not fields_payload:
            return None
        return fields_payload
