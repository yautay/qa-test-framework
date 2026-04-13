from __future__ import annotations

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from loguru import logger

from framework.env import load_env
from framework.integrations.jira import JiraAuth, JiraClient
from framework.logger import add_reporting_api_sink, configure_tools_logging
from framework.reporting_client import ReportingClient
from framework.visual.baseline_store import BaselineStore
from framework.visual.config.server import REPORT_SYNC_WORKERS

from .constants import DEFAULT_PORT, REPO_ROOT
from .context import ReportServerContext
from .http import _build_handler
from .paths import _discover_visual_run_dirs, _resolve_report_dir, _run_id_from_visual_dir
from .server import _resolve_sync_workers


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Serve visual reports with listing and baseline approval endpoints")
    parser.add_argument("--report-dir", default="", help="Path to visual report directory (artifacts/<run_id>/visual)")
    parser.add_argument("--run-id", default="", help="Run id under artifacts/<run_id>/visual")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    log_path = configure_tools_logging("report_server")
    logger.debug("tools_log_file", path=str(log_path), script="report_server")

    ui_dist_dir = (REPO_ROOT / "framework" / "visual" / "ui" / "dist").resolve()
    if not ui_dist_dir.is_dir():
        raise FileNotFoundError("UI build missing; run `npm run build` inside framework/visual/ui")

    run_dirs = _discover_visual_run_dirs(REPO_ROOT)
    selected_run_id = ""
    pinned_run_dirs: dict[str, Path] = {}
    if args.run_id or args.report_dir:
        selected_report_dir = _resolve_report_dir(REPO_ROOT, args.report_dir or None, args.run_id or None)
        selected_run_id = _run_id_from_visual_dir(REPO_ROOT, selected_report_dir)
        pinned_run_dirs[selected_run_id] = selected_report_dir

    env = load_env()
    reporting_enabled = bool(env.reporting_enabled)
    reporting_api_url = str(env.reporting_api_url or "").strip()
    sync_workers = _resolve_sync_workers(REPORT_SYNC_WORKERS)
    sync_executor = ThreadPoolExecutor(max_workers=sync_workers, thread_name_prefix="report-sync")
    reporting_client: ReportingClient | None = None
    if reporting_enabled:
        if not reporting_api_url:
            logger.error(
                "reporting_config_missing_url",
                message="reporting_enabled=true but REPORTING_API_URL is empty",
            )
            reporting_enabled = False
        else:
            reporting_client = ReportingClient(
                enabled=True,
                base_url=reporting_api_url,
                token=env.reporting_api_token,
                log_endpoint=env.reporting_api_log_endpoint,
                log_level=env.reporting_api_log_level,
                timeout_seconds=env.reporting_api_timeout_seconds,
                retries=env.reporting_api_retries,
            )
            add_reporting_api_sink(reporting_client, env.reporting_api_log_level)
    jira_client: JiraClient | None = None
    jira_auth_configured = False
    jira_url = str(env.jira_url or "").strip()
    jira_enabled = bool(env.jira_enabled)
    jira_mode = str(env.jira_auth_mode or "basic").strip().lower()
    if jira_enabled and jira_url:
        username = str(env.jira_username or "").strip()
        password = str(env.jira_password or "").strip()
        api_token = str(env.jira_api_token or "").strip()
        auth: JiraAuth | None = None
        if jira_mode == "token":
            if username and api_token:
                auth = JiraAuth(mode="token", username=username, password="", api_token=api_token)
        else:
            if username and password:
                auth = JiraAuth(mode="basic", username=username, password=password, api_token=api_token)
        if auth:
            jira_client = JiraClient(
                base_url=jira_url,
                verify_ssl=bool(env.jira_verify_ssl),
                auth=auth,
                timeout_seconds=max(5, int(float(env.jira_submit_timeout_ms) / 1000)),
            )
            jira_auth_configured = True
        else:
            logger.debug(
                "jira_auth_missing_credentials",
                mode=jira_mode,
                username=bool(username),
                api_token=bool(api_token),
            )
    context = ReportServerContext(
        repo_root=REPO_ROOT,
        ui_dist_dir=ui_dist_dir,
        baseline_store=BaselineStore(env, REPO_ROOT),
        run_dirs=run_dirs,
        pinned_run_dirs=pinned_run_dirs,
        reporting_client=reporting_client,
        reporting_enabled=reporting_enabled,
        reporting_bug_endpoint=str(cast(Any, env).reporting_api_bug_endpoint or "").strip(),
        reporting_aso_endpoint=str(cast(Any, env).reporting_api_aso_endpoint or "").strip(),
        sync_workers=sync_workers,
        sync_executor=sync_executor,
        pms_enabled=bool(env.pms_enabled),
        pms_base_url=str(env.pms_base_url or "").strip(),
        pms_timeout_sec=int(env.pms_timeout_sec),
        pms_health_timeout_seconds=int(env.pms_health_timeout_seconds),
        pms_retry_max=int(env.pms_retry_max),
        pms_poll_interval_ms=int(env.pms_poll_interval_ms),
        pms_poll_idle_multiplier=float(env.pms_poll_idle_multiplier),
        bug_pdf_config_path=(
            REPO_ROOT / "framework" / "visual" / "ui" / "src" / "config" / "bug_report_pdf_config.json"
        ),
        jira_enabled=jira_enabled,
        jira_url=jira_url,
        jira_verify_ssl=bool(env.jira_verify_ssl),
        jira_auth_mode=jira_mode,
        jira_auth_configured=jira_auth_configured,
        jira_retry_max=int(env.jira_retry_max),
        jira_submit_timeout_ms=max(10000, int(env.jira_submit_timeout_ms)),
        jira_upload_delay_seconds=float(env.jira_upload_delay_seconds),
        jira_pixel_diff_max_width_px=int(env.jira_pixel_diff_max_width_px),
        jira_aso_mentions=list(env.jira_aso_mentions),
        framework_mode=str(getattr(env, "framework_mode", "server") or "server").strip().lower(),
        jira_client=jira_client,
    )
    handler = _build_handler(context)
    server = ThreadingHTTPServer((args.host, int(args.port)), handler)

    print(f"ui dist dir: {ui_dist_dir}")
    if selected_run_id:
        print(f"selected report: {selected_run_id} -> {pinned_run_dirs.get(selected_run_id)}")
        print(f"server listening: http://{args.host}:{args.port}/reports/{selected_run_id}")
    else:
        print(f"server listening: http://{args.host}:{args.port}/")
    print(f"report sync workers: {sync_workers}")
    print(
        "endpoints: GET /api/app-info, GET /api/perceptual/queue, GET /api/perceptual/health, GET /api/reports, "
        "GET /api/reports/<run_id>/results, GET /api/reports/<run_id>/image/ref"
    )
    print(
        "endpoints: GET /api/builds/<run_id>/tags, "
        "POST /api/builds/<run_id>/events, "
        "POST /api/builds/<run_id>/lock/acquire, "
        "POST /api/builds/<run_id>/lock/heartbeat, "
        "POST /api/builds/<run_id>/lock/release, "
        "POST /api/builds/<run_id>/report, "
        "POST /api/reports/<run_id>/baseline/challenge, "
        "POST /api/reports/<run_id>/baseline/send, "
        "POST /api/reports/<run_id>/jira/comment"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutting down report server")
    finally:
        server.server_close()
        sync_executor.shutdown(wait=False, cancel_futures=False)
    return 0


__all__ = ["main"]
