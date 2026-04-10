from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

from framework.integrations.jira import JiraClient
from framework.reporting_client import ReportingClient
from framework.visual.baseline_store import BaselineStore

from .paths import _discover_visual_run_dirs, _is_ready_visual_dir


@dataclass
class ChallengeEntry:
    run_id: str
    phrase: str
    expires_at: float


@dataclass
class ReportServerContext:
    repo_root: Path
    ui_dist_dir: Path
    baseline_store: BaselineStore
    run_dirs: dict[str, Path]
    pinned_run_dirs: dict[str, Path] = field(default_factory=dict)
    challenges: dict[str, ChallengeEntry] = field(default_factory=dict)
    reporting_client: ReportingClient | None = None
    reporting_enabled: bool = False
    reporting_bug_endpoint: str = ""
    reporting_aso_endpoint: str = ""
    bug_pdf_config_path: Path | None = None
    sync_workers: int = 0
    sync_executor: Any = field(default=None, repr=False)
    pms_enabled: bool = False
    pms_base_url: str = ""
    pms_timeout_sec: int = 15
    pms_health_timeout_seconds: int = 2
    pms_retry_max: int = 2
    pms_poll_interval_ms: int = 5000
    pms_poll_idle_multiplier: float = 1.0
    _lock: Any = field(default_factory=Lock)
    jira_enabled: bool = False
    jira_url: str = ""
    jira_verify_ssl: bool = False
    jira_auth_mode: str = "basic"
    jira_auth_configured: bool = False
    jira_retry_max: int = 3
    jira_upload_delay_seconds: float = 1.0
    jira_pixel_diff_max_width_px: int = 320
    jira_aso_mentions: list[str] = field(default_factory=list)
    jira_client: JiraClient | None = None

    def resolve_run_dir(self, run_id: str) -> Path | None:
        with self._lock:
            existing = self.run_dirs.get(run_id)
            if existing is not None:
                return existing
        self.refresh_run_dirs()
        with self._lock:
            return self.run_dirs.get(run_id)

    def refresh_run_dirs(self) -> None:
        discovered = _discover_visual_run_dirs(self.repo_root)
        for run_id, report_dir in self.pinned_run_dirs.items():
            if _is_ready_visual_dir(report_dir):
                discovered[run_id] = report_dir
        with self._lock:
            self.run_dirs = discovered

    def list_run_dirs(self) -> dict[str, Path]:
        self.refresh_run_dirs()
        with self._lock:
            return dict(self.run_dirs)
