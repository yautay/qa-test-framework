from __future__ import annotations
from dataclasses import replace
import getpass
import json
import os
import socket
import time
import uuid
from datetime import datetime, timezone
import pytest
import settings_cli
from loguru import logger

from framework.artifacts import RunArtifacts, build_run_artifacts, resolve_artifacts_base_dir
from framework.env import RuntimeEnv, load_env
from framework.git_info import get_git_metadata
from framework.logger import configure_logging
from framework.reporting_client import ReportingClient
from framework.timing_monitor import (
    detect_slow_regressions,
    load_previous_timings,
    save_run_timings,
)


def _get_scenario_description(item: pytest.Item) -> str | None:
    marker = item.get_closest_marker("scenario")
    if marker is None:
        return None
    if marker.args:
        value = str(marker.args[0]).strip()
        return value or None
    value = str(marker.kwargs.get("description", "")).strip()
    return value or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_run_note(raw: object, source: str) -> str:
    text = str(raw or "").strip()
    if len(text) > 50:
        raise pytest.UsageError(f"{source} accepts at most 50 characters")
    return text


def _resolve_run_metadata(config: pytest.Config) -> dict[str, str]:
    cli_tester = str(config.getoption("--tester") or "").strip()
    cli_run_note_raw = config.getoption("--run_note")
    cli_run_note = _normalize_run_note(cli_run_note_raw, "--run_note")

    settings_tester = str(getattr(settings_cli, "tester", "") or "").strip()
    settings_run_note = _normalize_run_note(getattr(settings_cli, "run_note", ""), "settings_cli.run_note")

    tester = cli_tester if cli_tester else settings_tester
    run_note = cli_run_note if cli_run_note else settings_run_note
    return {
        "tester": tester,
        "run_note": run_note,
    }


def _write_run_metadata_file(artifacts: RunArtifacts, metadata: dict[str, str]) -> None:
    payload = {
        "tester": str(metadata.get("tester", "") or ""),
        "run_note": str(metadata.get("run_note", "") or ""),
    }
    target = artifacts.root / "run-metadata.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_run_profile(config: pytest.Config) -> str:
    markexpr = str(getattr(config.option, "markexpr", "") or "").strip()
    if markexpr == "aso":
        return "aso"
    if markexpr == "smoke":
        return "smoke"
    if markexpr == "visual":
        return "visual"
    if markexpr == "not aso":
        return "functional"
    if markexpr:
        return "custom"
    return "default"


def _build_source_context(env: RuntimeEnv, worker_id: str) -> dict[str, str]:
    host = socket.gethostname()
    user = os.getenv("USER") or os.getenv("USERNAME") or getpass.getuser()
    instance_id = f"{host}-{user}-{os.getpid()}"
    return {
        "project": env.reporting_source_project,
        "framework_version": env.framework_version,
        "instance_id": instance_id,
        "host": host,
        "user": user,
        "worker_id": worker_id,
        "origin": env.reporting_source_origin,
    }


def _derive_test_status(item: pytest.Item) -> str:
    rep_setup = getattr(item, "rep_setup", None)
    rep_call = getattr(item, "rep_call", None)
    rep_teardown = getattr(item, "rep_teardown", None)

    for report in (rep_setup, rep_teardown):
        if report and report.failed:
            return "error"

    if rep_call is None:
        return "skipped"

    wasxfail = bool(getattr(rep_call, "wasxfail", False))
    if rep_call.skipped:
        return "xfailed" if wasxfail else "skipped"
    if rep_call.failed:
        return "failed"
    if rep_call.passed:
        return "xpassed" if wasxfail else "passed"
    return "error"


def _base_url_resolver(config: pytest.Config):
    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return

    cli_server_type = (config.getoption("--server-type") or "").strip()
    cli_server_name = (config.getoption("--server-name") or "").strip()
    cli_base_url = (config.getoption("--base-url") or "").strip()

    if cli_server_type:
        env = replace(env, server_type=cli_server_type)
    if cli_server_name:
        env = replace(env, server_name=cli_server_name)

    if cli_base_url:
        config._runtime_env = replace(env, base_url=cli_base_url)
        return

    if settings_cli.base_url_override != "":
        config._runtime_env = replace(env, base_url=settings_cli.base_url_override)
        return

    if env.base_url:
        config._runtime_env = replace(env, base_url=env.base_url)


def pytest_configure(config: pytest.Config) -> None:
    env = load_env()
    artifacts_base_dir = resolve_artifacts_base_dir(env.artifacts_dir, config.rootpath)
    artifacts = build_run_artifacts(str(artifacts_base_dir))
    worker_id = os.getenv("PYTEST_XDIST_WORKER", "master")
    git_metadata = get_git_metadata()
    run_metadata = _resolve_run_metadata(config)
    configure_logging(
        artifacts.logs / "test_run.log",
        artifacts.run_id,
        env.browser,
        worker_id,
        git_metadata.user,
        git_metadata.email,
        run_metadata.get("tester", ""),
        run_metadata.get("run_note", ""),
    )

    config._runtime_env = env
    config._run_metadata = run_metadata
    config._run_artifacts = artifacts
    config._git_metadata = git_metadata
    config._reporting_client = ReportingClient(
        enabled=env.reporting_enabled,
        base_url=env.reporting_api_url,
        token=env.reporting_api_token,
        run_start_endpoint=env.reporting_api_run_start_endpoint,
        test_result_endpoint=env.reporting_api_test_result_endpoint,
        run_finish_endpoint=env.reporting_api_run_finish_endpoint,
        timeout_seconds=env.reporting_api_timeout_seconds,
        retries=env.reporting_api_retries,
    )
    config._test_case_timings = {}
    config._test_case_started_at = {}
    config._test_case_emitted = set()
    config._result_counters = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "error": 0,
    }
    config._run_start_payload = {}
    config._run_finish_payload = {"finished_at": None, "exit_status": None}
    config._session_started = time.time()
    config._reporting_suspended = any(
        bool(getattr(config.option, attr, False))
        for attr in (
            "fixtures",
            "showfixtures",
            "fixtures_per_test",
            "show_fixtures_per_test",
            "collectonly",
        )
    )
    _write_run_metadata_file(artifacts, run_metadata)


def pytest_sessionstart(session: pytest.Session) -> None:
    if getattr(session.config, "_reporting_suspended", False):
        return

    env: RuntimeEnv = session.config._runtime_env
    artifacts: RunArtifacts = session.config._run_artifacts
    metadata = session.config._git_metadata
    run_start_payload = {
        "schema_version": env.reporting_schema_version,
        "event_id": str(uuid.uuid4()),
        "event_type": "run_start",
        "event_time_utc": _utc_now(),
        "idempotency_key": f"run_start:{artifacts.run_id}:{os.getenv('PYTEST_XDIST_WORKER', 'master')}",
        "source": _build_source_context(env, os.getenv("PYTEST_XDIST_WORKER", "master")),
        "run_id": artifacts.run_id,
        "run_started_at": _utc_now(),
        "execution": {
            "browser": env.browser,
            "headless": env.headless,
            "grid_enabled": env.is_grid_available,
            "grid_endpoint": env.grid_ws_endpoint if env.is_grid_available else "",
            "viewport": str(getattr(session.config.option, "viewport", "fhd") or "fhd"),
            "profile": _resolve_run_profile(session.config),
        },
        "target": {
            "server_type": env.server_type,
            "server_name": env.server_name,
            "base_url": env.base_url,
        },
        "git": {
            "repo": "",
            "commit": metadata.commit,
            "branch": metadata.branch,
            "author_name": metadata.user,
            "author_email": metadata.email,
        },
        "metadata": session.config._run_metadata,
    }
    session.config._run_start_payload = run_start_payload
    logger.info("reporting_run_start", run_id=artifacts.run_id, **session.config._run_metadata)
    session.config._reporting_client.run_start(run_start_payload)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    artifacts: RunArtifacts = session.config._run_artifacts
    timings: dict[str, float] = session.config._test_case_timings
    durations_path = artifacts.logs / "test_durations.json"
    save_run_timings(durations_path, timings)

    previous = load_previous_timings(artifacts.root)
    for regression in detect_slow_regressions(timings, previous):
        logger.warning("test_case_slow_regression", **regression)

    run_finish_payload = {
        "schema_version": session.config._runtime_env.reporting_schema_version,
        "event_id": str(uuid.uuid4()),
        "event_type": "run_finish",
        "event_time_utc": _utc_now(),
        "idempotency_key": f"run_finish:{artifacts.run_id}:{os.getenv('PYTEST_XDIST_WORKER', 'master')}",
        "source": _build_source_context(
            session.config._runtime_env,
            os.getenv("PYTEST_XDIST_WORKER", "master"),
        ),
        "run_id": artifacts.run_id,
        "run_finished_at": _utc_now(),
        "exit_status": exitstatus,
        "duration_ms": int(
            max(0.0, time.time() - float(getattr(session.config, "_session_started", time.time()))) * 1000
        ),
        "summary": session.config._result_counters,
        "quality_signals": {
            "retry_count": 0,
            "flaky_count": 0,
            "slow_regression_count": 0,
        },
        "metadata": session.config._run_metadata,
    }
    session.config._run_finish_payload = run_finish_payload
    if not getattr(session.config, "_reporting_suspended", False):
        logger.info("reporting_run_finish", run_id=artifacts.run_id, **session.config._run_metadata)
        session.config._reporting_client.run_finish(run_finish_payload)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None):
    started = time.perf_counter()
    started_at = _utc_now()
    item.config._test_case_started_at[item.nodeid] = started_at
    scenario = _get_scenario_description(item)
    item._scenario_description = scenario
    outcome = yield
    _ = outcome
    duration_seconds = round(time.perf_counter() - started, 3)
    report = getattr(item, "rep_call", None)
    status = "unknown"
    if report is not None:
        status = report.outcome
    logger.info(
        "test_case_timing",
        nodeid=item.nodeid,
        duration_seconds=duration_seconds,
        status=status,
        scenario=scenario,
    )
    item.config._test_case_timings[item.nodeid] = duration_seconds


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item: pytest.Item) -> None:
    if item.nodeid in item.config._test_case_emitted:
        return

    env: RuntimeEnv = item.config._runtime_env
    run_artifacts: RunArtifacts = item.config._run_artifacts
    status = _derive_test_status(item)
    started_at = item.config._test_case_started_at.get(item.nodeid)
    finished_at = _utc_now()
    duration_seconds = float(item.config._test_case_timings.get(item.nodeid, 0.0))
    scenario = getattr(item, "_scenario_description", None)
    artifacts_payload = getattr(item, "_artifacts_payload", {})
    if not isinstance(artifacts_payload, dict):
        artifacts_payload = {}

    artifact_list: list[dict[str, object]] = []
    kind_map = {
        "trace": "trace",
        "video": "video",
        "screenshot_raw": "screenshot_raw",
        "screenshot_annotated": "screenshot_annotated",
        "visual_baseline": "visual_baseline",
        "visual_actual": "visual_actual",
        "visual_diff": "visual_diff",
        "visual_heatmap": "visual_heatmap",
    }
    for key, path in artifacts_payload.items():
        if not isinstance(path, str):
            continue
        artifact_list.append(
            {
                "kind": kind_map.get(key, "other"),
                "path": path,
                "uri": "",
                "sha256": "",
                "size_bytes": 0,
                "available": True,
            }
        )

    payload = {
        "schema_version": env.reporting_schema_version,
        "event_id": str(uuid.uuid4()),
        "event_type": "test_result",
        "event_time_utc": finished_at,
        "idempotency_key": f"test_result:{run_artifacts.run_id}:{item.nodeid}:1",
        "source": _build_source_context(env, os.getenv("PYTEST_XDIST_WORKER", "master")),
        "run_id": run_artifacts.run_id,
        "test_id": item.nodeid,
        "nodeid": item.nodeid,
        "status": status,
        "attempt": 1,
        "is_flaky": False,
        "timing": {
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_ms": int(duration_seconds * 1000),
        },
        "scenario": scenario,
        "markers": [mark.name for mark in item.iter_markers()],
        "artifacts": artifact_list,
        "run_context": {
            "run_start": item.config._run_start_payload,
            "run_finish": item.config._run_finish_payload,
        },
        "metadata": item.config._run_metadata,
    }

    visual_payload = getattr(item, "_visual_payload", None)
    if isinstance(visual_payload, dict):
        payload["visual"] = visual_payload

    if not getattr(item.config, "_reporting_suspended", False):
        logger.info(
            "reporting_test_result",
            run_id=run_artifacts.run_id,
            nodeid=item.nodeid,
            status=status,
            **item.config._run_metadata,
        )
        item.config._reporting_client.test_result(payload)
    item.config._test_case_emitted.add(item.nodeid)
    counters = item.config._result_counters
    counters["total"] += 1
    if status in counters:
        counters[status] += 1


@pytest.fixture(scope="session")
def runtime_env(pytestconfig: pytest.Config) -> RuntimeEnv:
    """Resolved runtime configuration shared by all tests."""
    return pytestconfig._runtime_env


@pytest.fixture(scope="session")
def run_artifacts(pytestconfig: pytest.Config) -> RunArtifacts:
    """Run-scoped artifact paths (logs, traces, screenshots, videos)."""
    return pytestconfig._run_artifacts
