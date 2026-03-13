from __future__ import annotations

import getpass
import hashlib
import json
import os
import socket
import time
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from loguru import logger

import settings_cli
from framework.artifacts import RunArtifacts, build_run_artifacts, resolve_artifacts_base_dir
from framework.env import RuntimeEnv, load_env
from framework.git_info import get_git_metadata
from framework.logger import add_reporting_api_sink, bind_test_context, configure_logging
from framework.reporting_client import ReportingClient
from framework.targeting import resolve_target_context, resolve_target_id_for_nodeid
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
    return datetime.now(UTC).isoformat()


def _current_worker_id() -> str:
    return os.getenv("PYTEST_XDIST_WORKER", "master")


def _is_xdist_worker(config: pytest.Config) -> bool:
    worker_id = str(os.getenv("PYTEST_XDIST_WORKER") or "").strip()
    if worker_id and worker_id != "master":
        return True
    return hasattr(config, "workerinput")


def _is_xdist_controller(config: pytest.Config) -> bool:
    return bool(config.pluginmanager.hasplugin("xdist") and not _is_xdist_worker(config))


def _resolve_shared_run_id(config: pytest.Config) -> str | None:
    worker_input = getattr(config, "workerinput", None)
    if isinstance(worker_input, dict):
        token = str(worker_input.get("run_id") or "").strip()
        if token:
            return token
    shared_run_id = str(getattr(config, "_shared_run_id", "") or "").strip()
    if shared_run_id:
        return shared_run_id
    if _is_xdist_worker(config):
        raise pytest.UsageError("xdist worker missing shared run_id in workerinput")
    return None


def _resolve_shared_run_uid(config: pytest.Config) -> str | None:
    worker_input = getattr(config, "workerinput", None)
    if isinstance(worker_input, dict):
        token = str(worker_input.get("run_uid") or "").strip()
        if token:
            return token
    shared_run_uid = str(getattr(config, "_shared_run_uid", "") or "").strip()
    if shared_run_uid:
        return shared_run_uid
    if _is_xdist_worker(config):
        raise pytest.UsageError("xdist worker missing shared run_uid in workerinput")
    return None


def _load_worker_timing_files(logs_dir: Path) -> dict[str, float]:
    merged: dict[str, float] = {}
    for path in sorted(logs_dir.glob("test_durations_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        cases = payload.get("cases", {}) if isinstance(payload, dict) else {}
        if not isinstance(cases, dict):
            continue
        for nodeid, seconds in cases.items():
            if not isinstance(nodeid, str):
                continue
            try:
                merged[nodeid] = float(seconds)
            except (TypeError, ValueError):
                continue
    return merged


def _normalize_run_note(raw: object, source: str) -> str:
    text = str(raw or "").strip()
    if len(text) > 50:
        raise pytest.UsageError(f"{source} accepts at most 50 characters")
    return text


_ENV_ALIAS_TOKENS = {"demo", "prod", "local"}


def _normalize_target_selector(server_name: str) -> tuple[str, str]:
    """Resolve effective target selector from server_name.

    Returns: (resolved_server_name, source_kind)
    source_kind is either "server_name_alias" or "server_name".
    """

    token = str(server_name or "").strip().lower()
    if token in _ENV_ALIAS_TOKENS:
        return token, "server_name_alias"
    return token, "server_name"


def _normalize_reference_selector(reference_host: str) -> tuple[str, str]:
    """Resolve reference selector from a token used by visual dual-pass.

    Returns: (resolved_reference_host, source_kind)
    source_kind is either "reference_alias" or "reference_host".
    """

    token = str(reference_host or "").strip().lower()
    if token in _ENV_ALIAS_TOKENS:
        return token, "reference_alias"
    return token, "reference_host"


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
    producer_id = str(getattr(env, "reporting_source_producer_id", "") or "").strip() or host
    return {
        "project": env.reporting_source_project,
        "framework_version": env.framework_version,
        "producer_id": producer_id,
        "instance_id": instance_id,
        "host": host,
        "user": user,
        "worker_id": worker_id,
        "origin": env.reporting_source_origin,
    }


def _build_idempotency_key(
    *,
    event_type: str,
    run_uid: str,
    worker_id: str,
    test_id: str = "",
    attempt: int = 1,
) -> str:
    token = str(event_type or "").strip().lower()
    if token == "test_result":
        return f"test_result:{run_uid}:{test_id}:{int(attempt)}"
    if token in {"run_start", "run_finish"}:
        return f"{token}:{run_uid}:{worker_id}"
    return f"{token}:{run_uid}:{worker_id}"


def _build_event_envelope(
    *,
    env: RuntimeEnv,
    run_id: str,
    run_uid: str,
    event_type: str,
    worker_id: str,
    metadata: dict[str, str],
    event_time: str | None = None,
    test_id: str = "",
    attempt: int = 1,
) -> dict[str, object]:
    event_time_utc = str(event_time or _utc_now())
    return {
        "schema_version": env.reporting_schema_version,
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_time_utc": event_time_utc,
        "idempotency_key": _build_idempotency_key(
            event_type=event_type,
            run_uid=run_uid,
            worker_id=worker_id,
            test_id=test_id,
            attempt=attempt,
        ),
        "source": _build_source_context(env, worker_id),
        "run_id": run_id,
        "run_uid": run_uid,
        "metadata": metadata,
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


def _extract_pytest_outcome(item: pytest.Item) -> dict[str, str]:
    reports = {
        "setup": getattr(item, "rep_setup", None),
        "call": getattr(item, "rep_call", None),
        "teardown": getattr(item, "rep_teardown", None),
    }
    for phase in ("setup", "call", "teardown"):
        report = reports.get(phase)
        if report is None:
            continue
        outcome = str(getattr(report, "outcome", "") or "").strip().lower()
        if outcome in {"passed", ""}:
            continue
        longrepr_text = str(getattr(report, "longreprtext", "") or "").strip()
        if not longrepr_text:
            try:
                longrepr_text = str(getattr(report, "longrepr", "") or "").strip()
            except Exception:
                longrepr_text = ""
        first_line = ""
        for line in longrepr_text.splitlines():
            token = str(line or "").strip()
            if token:
                first_line = token
                break
        if not first_line:
            first_line = f"pytest {phase} {outcome}"
        return {
            "phase": phase,
            "outcome": outcome,
            "message": first_line[:300],
            "longrepr": longrepr_text[:2500],
        }
    return {}


def _sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_entry(kind: str, path: str) -> dict[str, object]:
    path_token = str(path or "").strip()
    available = False
    size_bytes = 0
    size_mib = 0.0
    sha256 = ""
    if path_token:
        artifact_path = Path(path_token)
        if artifact_path.is_file():
            available = True
            try:
                size_bytes = int(artifact_path.stat().st_size)
                size_mib = round(size_bytes / (1024 * 1024), 3)
            except OSError:
                size_bytes = 0
                size_mib = 0.0
            try:
                sha256 = _sha256_for_file(artifact_path)
            except OSError:
                sha256 = ""
    return {
        "kind": kind,
        "path": path_token,
        "uri": "",
        "sha256": sha256,
        "size_bytes": size_bytes,
        "size_mib": size_mib,
        "available": available,
    }


def _test_result_payloads_path(run_artifacts: RunArtifacts, worker_id: str) -> Path:
    return run_artifacts.root / "workers" / worker_id / "test_result_payloads.json"


def _persist_test_result_payload(config: pytest.Config, nodeid: str, payload: dict[str, object]) -> None:
    payloads = getattr(config, "_test_result_payloads", None)
    if not isinstance(payloads, dict):
        payloads = {}
        config._test_result_payloads = payloads
    payloads[nodeid] = payload

    run_artifacts = getattr(config, "_run_artifacts", None)
    if not isinstance(run_artifacts, RunArtifacts):
        return

    worker_id = _current_worker_id()
    target = _test_result_payloads_path(run_artifacts, worker_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payloads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)


def _deduplicated_markers(item: pytest.Item) -> list[str]:
    markers = [str(mark.name) for mark in item.iter_markers() if str(mark.name or "").strip()]
    return list(dict.fromkeys(markers))


def _read_perceptual_quality_signals(run_root: Path) -> dict[str, object]:
    default = {
        "pms_used": False,
        "pms_jobs_submitted": 0,
        "pms_jobs_done": 0,
        "pms_jobs_error": 0,
        "pms_jobs_skipped": 0,
        "pms_unavailable_reason": "",
    }
    status_path = run_root / "visual" / "perceptual-status.json"
    if not status_path.is_file():
        return default
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default
    if not isinstance(payload, dict):
        return default

    def _as_int(value: object) -> int:
        try:
            return max(0, int(cast(Any, value)))
        except (TypeError, ValueError):
            return 0

    done = _as_int(payload.get("done_count"))
    error = _as_int(payload.get("error_count"))
    submitted = _as_int(payload.get("submitted_count", done + error))
    skipped = _as_int(payload.get("skipped_count"))
    reason = str(payload.get("unavailable_reason", "") or "")
    used = bool(payload.get("used", False)) or submitted > 0
    return {
        "pms_used": used,
        "pms_jobs_submitted": submitted,
        "pms_jobs_done": done,
        "pms_jobs_error": error,
        "pms_jobs_skipped": skipped,
        "pms_unavailable_reason": reason,
    }


def _base_url_resolver(config: pytest.Config):
    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return

    cli_server_name = (config.getoption("--server-name") or "").strip()
    cli_base_url = (config.getoption("--base-url") or "").strip()
    cli_reference_host = (config.getoption("--reference-host") or "").strip()

    if cli_server_name:
        env = replace(env, server_name=cli_server_name)
    if cli_reference_host:
        env = replace(env, reference_host=cli_reference_host)

    normalized_server_name, target_source = _normalize_target_selector(env.server_name)
    if normalized_server_name != env.server_name:
        logger.info(
            "runtime_target_resolved",
            source=target_source,
            requested_server_name=env.server_name,
            resolved_server_name=normalized_server_name,
        )
        env = replace(
            env,
            server_name=normalized_server_name,
        )

    reference_host = str(getattr(env, "reference_host", "") or "").strip()
    if reference_host:
        resolved_reference_host, ref_source = _normalize_reference_selector(reference_host)
        logger.info(
            "runtime_reference_resolved",
            source=ref_source,
            reference_host=reference_host,
            resolved_reference_host=resolved_reference_host,
        )

    if cli_base_url:
        config._runtime_env = replace(env, base_url=cli_base_url)
        return

    if settings_cli.base_url_override != "":
        config._runtime_env = replace(env, base_url=settings_cli.base_url_override)
        return

    config._runtime_env = env


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    explicit_base_url = str(getattr(env, "base_url", "") or "")
    explicit_base_url = (explicit_base_url or "").strip()
    if explicit_base_url:
        return

    issues: list[str] = []
    for item in items:
        marker = item.get_closest_marker("target")
        marker_target = ""
        if marker and marker.args:
            marker_target = str(marker.args[0] or "").strip()
        nodeid = str(getattr(item, "nodeid", "") or "")
        try:
            target_id = marker_target or resolve_target_id_for_nodeid(nodeid)
        except ValueError as exc:
            issues.append(str(exc))
            continue
        if target_id:
            continue
        normalized = nodeid.replace("\\", "/")
        if normalized.startswith("qa/visual/") or normalized.startswith("qa/e2e/netcorner/"):
            issues.append(
                "Cannot resolve target for nodeid="
                f"{nodeid!r}; add @pytest.mark.target('<id>') or extend path mapping in framework.targeting.registry"
            )

    if issues:
        details = "\n".join(f"- {issue}" for issue in sorted(set(issues)))
        raise pytest.UsageError(f"Target resolution errors (strict mode):\n{details}")


def pytest_configure(config: pytest.Config) -> None:
    env = replace(load_env(), ignore_https_errors=True)
    artifacts_base_dir = resolve_artifacts_base_dir(env.artifacts_dir, config.rootpath)
    artifacts = build_run_artifacts(str(artifacts_base_dir), run_id=_resolve_shared_run_id(config))
    run_uid = _resolve_shared_run_uid(config) or str(uuid.uuid4())
    config._shared_run_uid = run_uid
    config._run_uid = run_uid
    os.environ.setdefault("PYTEST_XDIST_RUN_UID", run_uid)
    worker_id = _current_worker_id()
    git_metadata = get_git_metadata()
    run_metadata = _resolve_run_metadata(config)
    configure_logging(
        artifacts.logs,
        artifacts.run_id,
        env.browser,
        worker_id,
        git_metadata.user,
        git_metadata.email,
        run_metadata.get("tester", ""),
        run_metadata.get("run_note", ""),
    )

    config._runtime_env = env
    _base_url_resolver(config)
    env = config._runtime_env
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
        log_endpoint=env.reporting_api_log_endpoint,
        log_level=env.reporting_api_log_level,
        timeout_seconds=env.reporting_api_timeout_seconds,
        retries=env.reporting_api_retries,
        async_enabled=env.reporting_async_enabled,
        async_queue_maxsize=env.reporting_async_queue_maxsize,
        async_max_attempts=env.reporting_async_max_attempts,
        async_max_retry_age_seconds=env.reporting_async_max_retry_age_seconds,
        async_flush_timeout_seconds=env.reporting_async_flush_timeout_seconds,
        source_host=socket.gethostname(),
        source_user=os.getenv("USER") or os.getenv("USERNAME") or getpass.getuser(),
    )
    add_reporting_api_sink(config._reporting_client, env.reporting_api_log_level)
    config._test_case_timings = {}
    config._test_case_started_at = {}
    config._test_case_started_perf = {}
    config._test_case_emitted = set()
    config._test_result_payloads = {}
    config._result_counters = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
        "error": 0,
    }
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
    metadata_path = artifacts.root / "run-metadata.json"
    if (not _is_xdist_worker(config)) or (not metadata_path.exists()):
        _write_run_metadata_file(artifacts, run_metadata)


def pytest_configure_node(node) -> None:
    artifacts = getattr(node.config, "_run_artifacts", None)
    if artifacts is None:
        return
    node.workerinput["run_id"] = artifacts.run_id
    node.workerinput["run_uid"] = str(getattr(node.config, "_run_uid", "") or "")


def pytest_sessionstart(session: pytest.Session) -> None:
    if getattr(session.config, "_reporting_suspended", False):
        return

    env: RuntimeEnv = session.config._runtime_env
    artifacts: RunArtifacts = session.config._run_artifacts
    run_uid = str(getattr(session.config, "_run_uid", "") or "")
    worker_id = os.getenv("PYTEST_XDIST_WORKER", "master")
    metadata = session.config._git_metadata
    run_start_payload = {
        **_build_event_envelope(
            env=env,
            run_id=artifacts.run_id,
            run_uid=run_uid,
            event_type="run_start",
            worker_id=worker_id,
            metadata=session.config._run_metadata,
        ),
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
    }
    logger.info("reporting_run_start", run_id=artifacts.run_id, **session.config._run_metadata)
    session.config._reporting_client.run_start(run_start_payload)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    artifacts: RunArtifacts = session.config._run_artifacts
    run_uid = str(getattr(session.config, "_run_uid", "") or "")
    timings: dict[str, float] = session.config._test_case_timings
    worker_id = _current_worker_id()
    if _is_xdist_worker(session.config):
        durations_path = artifacts.logs / f"test_durations_{worker_id}.json"
        save_run_timings(durations_path, timings)
    elif _is_xdist_controller(session.config):
        merged_timings = _load_worker_timing_files(artifacts.logs)
        durations_path = artifacts.logs / "test_durations.json"
        save_run_timings(durations_path, merged_timings)
        timings = merged_timings
    else:
        durations_path = artifacts.logs / "test_durations.json"
        save_run_timings(durations_path, timings)

    previous = load_previous_timings(artifacts.root)
    for regression in detect_slow_regressions(timings, previous):
        logger.warning("test_case_slow_regression", **regression)

    run_finish_payload = {
        **_build_event_envelope(
            env=session.config._runtime_env,
            run_id=artifacts.run_id,
            run_uid=run_uid,
            event_type="run_finish",
            worker_id=os.getenv("PYTEST_XDIST_WORKER", "master"),
            metadata=session.config._run_metadata,
        ),
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
            **_read_perceptual_quality_signals(artifacts.root),
        },
    }
    if not getattr(session.config, "_reporting_suspended", False):
        logger.info("reporting_run_finish", run_id=artifacts.run_id, **session.config._run_metadata)
        session.config._reporting_client.run_finish(run_finish_payload)
    session.config._reporting_client.flush(
        timeout_seconds=session.config._runtime_env.reporting_async_flush_timeout_seconds
    )
    session.config._reporting_client.shutdown(
        timeout_seconds=session.config._runtime_env.reporting_async_flush_timeout_seconds
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None):
    started = time.perf_counter()
    started_at = _utc_now()
    item.config._test_case_started_at[item.nodeid] = started_at
    item.config._test_case_started_perf[item.nodeid] = started
    scenario = _get_scenario_description(item)
    item._scenario_description = scenario
    outcome = yield
    _ = outcome
    duration_seconds = round(time.perf_counter() - started, 3)
    report = getattr(item, "rep_call", None)
    status = "unknown"
    if report is not None:
        status = report.outcome
    test_logger = bind_test_context(item.nodeid)
    test_logger.info(
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
    run_uid = str(getattr(item.config, "_run_uid", "") or "")
    status = _derive_test_status(item)
    started_at = item.config._test_case_started_at.get(item.nodeid)
    finished_at = _utc_now()
    duration_seconds = float(item.config._test_case_timings.get(item.nodeid, 0.0))
    if duration_seconds <= 0:
        started_perf = item.config._test_case_started_perf.get(item.nodeid)
        if isinstance(started_perf, (int, float)):
            duration_seconds = max(0.0, time.perf_counter() - float(started_perf))
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
        "visual_reference_actual": "visual_reference_actual",
        "visual_reference_baseline": "visual_reference_baseline",
    }
    for key, path in artifacts_payload.items():
        if not isinstance(path, str):
            continue
        artifact_list.append(_artifact_entry(kind_map.get(key, "other"), path))

    payload = {
        **_build_event_envelope(
            env=env,
            run_id=run_artifacts.run_id,
            run_uid=run_uid,
            event_type="test_result",
            worker_id=os.getenv("PYTEST_XDIST_WORKER", "master"),
            metadata=item.config._run_metadata,
            event_time=finished_at,
            test_id=item.nodeid,
            attempt=1,
        ),
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
        "markers": _deduplicated_markers(item),
        "artifacts": artifact_list,
    }

    pytest_outcome = _extract_pytest_outcome(item)
    if pytest_outcome:
        payload["pytest_outcome"] = pytest_outcome

    visual_payload = getattr(item, "_visual_payload", None)
    if isinstance(visual_payload, dict):
        payload["visual"] = visual_payload

    _persist_test_result_payload(item.config, item.nodeid, payload)

    if not getattr(item.config, "_reporting_suspended", False):
        test_logger = bind_test_context(item.nodeid)
        test_logger.info(
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


@pytest.fixture(scope="function")
def target_context(request: pytest.FixtureRequest, runtime_env: RuntimeEnv):
    marker = request.node.get_closest_marker("target")
    marker_target = ""
    if marker and marker.args:
        marker_target = str(marker.args[0] or "").strip()

    try:
        return resolve_target_context(
            nodeid=request.node.nodeid,
            server_name=runtime_env.server_name,
            explicit_base_url=runtime_env.base_url,
            marker_target=marker_target,
        )
    except ValueError as exc:
        raise pytest.UsageError(str(exc)) from exc


@pytest.fixture(scope="function")
def base_url(target_context) -> str:
    return str(target_context.base_url or "")


@pytest.fixture(scope="session")
def run_artifacts(pytestconfig: pytest.Config) -> RunArtifacts:
    """Run-scoped artifact paths (logs, traces, screenshots, videos)."""
    return pytestconfig._run_artifacts
