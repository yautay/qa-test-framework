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
from urllib.parse import urljoin

import pytest
import requests
from loguru import logger

import settings_cli
from framework.artifacts import RunArtifacts, build_run_artifacts, resolve_artifacts_base_dir
from framework.browser import BrowserSession
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

_FORBIDDEN_PLUGIN_PATTERNS: tuple[tuple[str, str], ...] = (
    ("anyio", "plugin anyio can force asyncio loop and conflicts with Playwright Sync API"),
    ("playwright", "plugin pytest-playwright is disabled because project uses custom Playwright fixtures"),
    (
        "pytest_playwright",
        "plugin pytest-playwright is disabled because project uses custom Playwright fixtures",
    ),
    ("base_url", "plugin pytest-base-url is disabled because project uses custom base_url resolution"),
    (
        "pytest_base_url",
        "plugin pytest-base-url is disabled because project uses custom base_url resolution",
    ),
)


def _iter_loaded_plugins(config: pytest.Config) -> list[tuple[str, str]]:
    loaded: list[tuple[str, str]] = []
    plugin_manager = config.pluginmanager
    is_blocked = getattr(plugin_manager, "is_blocked", None)
    for raw_name, plugin in plugin_manager.list_name_plugin():
        name = str(raw_name or "").strip()
        if not name:
            continue
        if callable(is_blocked):
            try:
                if bool(is_blocked(name)):
                    continue
            except Exception:
                pass
        if plugin is None:
            continue
        module_name = str(getattr(plugin, "__name__", "") or "").strip()
        if not module_name:
            module_name = str(type(plugin).__name__)
        loaded.append((name.lower(), module_name.lower()))
    return loaded


def _assert_supported_plugin_profile(config: pytest.Config) -> None:
    forbidden: list[str] = []
    for plugin_name, module_name in _iter_loaded_plugins(config):
        token = f"{plugin_name} {module_name}".strip()
        for pattern, reason in _FORBIDDEN_PLUGIN_PATTERNS:
            if pattern in token:
                forbidden.append(f"{plugin_name} ({module_name}) -> {reason}")
                break
    if not forbidden:
        return
    details = "\n".join(f"- {item}" for item in sorted(set(forbidden)))
    raise pytest.UsageError(
        "Unsupported pytest plugin profile for this project. "
        "Disable conflicting plugins in run configuration.\n"
        f"{details}"
    )


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


def _resolve_run_metadata(config: pytest.Config) -> dict[str, Any]:
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
        "target_git_info": _default_target_git_info(),
    }


def _default_target_git_info() -> dict[str, Any]:
    now = _utc_now()
    return {
        "frontend": {
            "branch": "",
            "commit": "",
            "endpoint": "/git-info",
            "url": "",
            "status": "not_configured",
            "error": "",
            "fetched_at_utc": now,
        },
        "backend": {
            "branch": "",
            "commit": "",
            "endpoint": "/git-info",
            "url": "",
            "status": "not_configured",
            "error": "",
            "fetched_at_utc": now,
        },
    }


def _resolve_git_info_url(*, base_url: str, explicit_url: str, endpoint: str) -> str:
    explicit = str(explicit_url or "").strip()
    if explicit:
        return explicit

    endpoint_token = str(endpoint or "").strip()
    if endpoint_token.startswith(("http://", "https://")):
        return endpoint_token

    base = str(base_url or "").strip()
    if not base:
        return ""
    return urljoin(base.rstrip("/") + "/", endpoint_token.lstrip("/"))


def _extract_git_info_fields(payload: dict[str, Any]) -> tuple[str, str]:
    branch = ""
    commit = ""
    branch_keys = ("branch", "baranch", "git_branch", "branch_name")
    commit_keys = ("commit", "commit_hash", "hash", "sha")

    for key in branch_keys:
        value = str(payload.get(key, "") or "").strip()
        if value:
            branch = value
            break

    for key in commit_keys:
        value = str(payload.get(key, "") or "").strip()
        if value:
            commit = value
            break

    git_section = payload.get("git")
    if isinstance(git_section, dict):
        if not branch:
            for key in branch_keys:
                value = str(git_section.get(key, "") or "").strip()
                if value:
                    branch = value
                    break
        if not commit:
            for key in commit_keys:
                value = str(git_section.get(key, "") or "").strip()
                if value:
                    commit = value
                    break

    return branch, commit


def _capture_git_info_endpoint(
    *,
    target: str,
    base_url: str,
    explicit_url: str,
    endpoint: str,
    timeout_seconds: int,
    ignore_https_errors: bool,
) -> dict[str, Any]:
    endpoint_token = str(endpoint or "").strip() or "/git-info"
    url = _resolve_git_info_url(base_url=base_url, explicit_url=explicit_url, endpoint=endpoint_token)
    payload = {
        "branch": "",
        "commit": "",
        "endpoint": endpoint_token,
        "url": url,
        "status": "not_configured",
        "error": "",
        "fetched_at_utc": _utc_now(),
    }
    if not url:
        return payload

    payload["status"] = "error"
    timeout = max(1, int(timeout_seconds or 3))
    try:
        response = requests.get(
            url,
            timeout=timeout,
            verify=not ignore_https_errors,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        payload["error"] = str(exc)
        logger.warning(
            "target_git_info_fetch_failed",
            target=target,
            endpoint=endpoint_token,
            url=url,
            timeout_seconds=timeout,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        return payload

    payload["url"] = str(response.url or url)
    if int(response.status_code) < 200 or int(response.status_code) >= 300:
        preview = ""
        try:
            preview = str(response.text or "")[:200]
        except Exception:
            preview = ""
        payload["error"] = f"unexpected_status:{response.status_code}"
        logger.warning(
            "target_git_info_invalid_http_status",
            target=target,
            endpoint=endpoint_token,
            url=payload["url"],
            status_code=int(response.status_code),
            response_preview=preview,
        )
        return payload

    try:
        body = response.json()
    except ValueError as exc:
        payload["error"] = "invalid_json"
        logger.warning(
            "target_git_info_invalid_json",
            target=target,
            endpoint=endpoint_token,
            url=payload["url"],
            error=str(exc),
            error_type=type(exc).__name__,
        )
        return payload

    if not isinstance(body, dict):
        payload["status"] = "invalid_payload"
        payload["error"] = "payload_not_object"
        logger.warning(
            "target_git_info_invalid_payload",
            target=target,
            endpoint=endpoint_token,
            url=payload["url"],
            payload_type=type(body).__name__,
        )
        return payload

    branch, commit = _extract_git_info_fields(body)
    payload["branch"] = branch
    payload["commit"] = commit
    if branch and commit:
        payload["status"] = "ok"
        payload["error"] = ""
        return payload

    payload["status"] = "invalid_payload"
    payload["error"] = "missing_branch_or_commit"
    logger.warning(
        "target_git_info_missing_required_fields",
        target=target,
        endpoint=endpoint_token,
        url=payload["url"],
        has_branch=bool(branch),
        has_commit=bool(commit),
    )
    return payload


def _capture_target_git_info(env: RuntimeEnv) -> dict[str, Any]:
    default_payload = _default_target_git_info()
    timeout_seconds = max(1, int(getattr(env, "run_git_info_timeout_seconds", 3) or 3))
    frontend_endpoint = str(getattr(env, "run_git_info_frontend_endpoint", "/git-info") or "/git-info")
    backend_endpoint = str(getattr(env, "run_git_info_backend_endpoint", "/git-info") or "/git-info")

    try:
        frontend = _capture_git_info_endpoint(
            target="frontend",
            base_url=str(getattr(env, "base_url", "") or ""),
            explicit_url=str(getattr(env, "run_git_info_frontend_url", "") or ""),
            endpoint=frontend_endpoint,
            timeout_seconds=timeout_seconds,
            ignore_https_errors=bool(getattr(env, "ignore_https_errors", True)),
        )
    except Exception as exc:
        frontend = dict(default_payload["frontend"])
        frontend["status"] = "error"
        frontend["error"] = f"unexpected_error:{type(exc).__name__}"
        frontend["fetched_at_utc"] = _utc_now()
        logger.warning(
            "target_git_info_unexpected_error",
            target="frontend",
            endpoint=frontend_endpoint,
            error=str(exc),
            error_type=type(exc).__name__,
        )

    try:
        backend = _capture_git_info_endpoint(
            target="backend",
            base_url="",
            explicit_url=str(getattr(env, "run_git_info_backend_url", "") or ""),
            endpoint=backend_endpoint,
            timeout_seconds=timeout_seconds,
            ignore_https_errors=bool(getattr(env, "ignore_https_errors", True)),
        )
    except Exception as exc:
        backend = dict(default_payload["backend"])
        backend["status"] = "error"
        backend["error"] = f"unexpected_error:{type(exc).__name__}"
        backend["fetched_at_utc"] = _utc_now()
        logger.warning(
            "target_git_info_unexpected_error",
            target="backend",
            endpoint=backend_endpoint,
            error=str(exc),
            error_type=type(exc).__name__,
        )

    default_payload["frontend"] = frontend
    default_payload["backend"] = backend
    return default_payload


def _capture_environment_probe(base_url: str, ignore_https_errors: bool) -> dict[str, Any]:
    request_url = str(base_url or "").strip()
    payload: dict[str, Any] = {
        "request_url": request_url,
        "method": "GET",
        "status_code": None,
        "final_url": "",
        "headers": {},
        "captured_at_utc": _utc_now(),
        "error": "",
    }
    if not request_url:
        payload["error"] = "base_url is empty"
        return payload

    try:
        response = requests.get(
            request_url,
            timeout=10,
            verify=not ignore_https_errors,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        payload["error"] = str(exc)
        return payload

    payload["status_code"] = int(response.status_code)
    payload["final_url"] = str(response.url or "")
    headers: dict[str, str] = {}
    for key, value in response.headers.items():
        headers[str(key)] = str(value)
    payload["headers"] = headers
    return payload


def _probe_is_resolved(probe: object) -> bool:
    if not isinstance(probe, dict):
        return False
    request_url = str(probe.get("request_url", "") or "").strip()
    return bool(request_url)


def _replace_with_retry(temp: Path, target: Path, *, retries: int = 6, base_delay_seconds: float = 0.05) -> None:
    last_error: PermissionError | None = None
    for attempt in range(retries):
        try:
            temp.replace(target)
            return
        except PermissionError as exc:
            last_error = exc
            if attempt >= retries - 1:
                break
            time.sleep(base_delay_seconds * (attempt + 1))
    if last_error is not None:
        raise last_error


def _worker_environment_probe_path(run_artifacts: RunArtifacts, worker_id: str) -> Path:
    return run_artifacts.root / "workers" / worker_id / "environment_probe.json"


def _write_worker_environment_probe_file(run_artifacts: RunArtifacts, worker_id: str, probe: dict[str, Any]) -> None:
    target = _worker_environment_probe_path(run_artifacts, worker_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".json.tmp")
    payload = {"environment_probe": dict(probe)}
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _replace_with_retry(temp, target)


def _resolve_probe_base_url_from_items(config: pytest.Config, items: list[pytest.Item]) -> tuple[str, str]:
    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return "", "runtime_env is not initialized"

    explicit_base_url = str(getattr(env, "base_url", "") or "").strip()
    if explicit_base_url:
        return explicit_base_url, "runtime_env.base_url"

    resolved_urls: set[str] = set()
    for item in items:
        marker = item.get_closest_marker("target")
        marker_target = ""
        if marker and marker.args:
            marker_target = str(marker.args[0] or "").strip()
        try:
            target = resolve_target_context(
                nodeid=str(getattr(item, "nodeid", "") or ""),
                server_name=env.server_name,
                explicit_base_url="",
                marker_target=marker_target,
            )
        except ValueError:
            continue
        token = str(getattr(target, "base_url", "") or "").strip()
        if token:
            resolved_urls.add(token)

    if len(resolved_urls) == 1:
        return next(iter(resolved_urls)), "target_mapping"
    if len(resolved_urls) > 1:
        sorted_urls = sorted(resolved_urls)
        chosen = sorted_urls[0]
        values = ", ".join(sorted_urls)
        return chosen, f"target_mapping_first_of_many: {values}"
    return "", "cannot resolve base_url from collected tests"


def _resolve_probe_base_url_from_runtime_items(items: list[pytest.Item]) -> tuple[str, str]:
    resolved_urls: set[str] = set()
    for item in items:
        funcargs = getattr(item, "funcargs", None)
        if isinstance(funcargs, dict):
            runtime_base_url = str(funcargs.get("base_url", "") or "").strip()
            if runtime_base_url:
                resolved_urls.add(runtime_base_url)
                continue

        visual_payload = getattr(item, "_visual_payload", None)
        if isinstance(visual_payload, dict):
            execution = visual_payload.get("execution")
            if isinstance(execution, dict):
                runtime_target_base_url = str(execution.get("target_base_url", "") or "").strip()
                if runtime_target_base_url:
                    resolved_urls.add(runtime_target_base_url)

    if len(resolved_urls) == 1:
        return next(iter(resolved_urls)), "runtime_item_base_url"
    if len(resolved_urls) > 1:
        sorted_urls = sorted(resolved_urls)
        chosen = sorted_urls[0]
        values = ", ".join(sorted_urls)
        return chosen, f"runtime_item_first_of_many: {values}"
    return "", "runtime item base_url is not available"


def _refresh_environment_probe_metadata(config: pytest.Config, items: list[pytest.Item]) -> None:
    if bool(getattr(config, "_environment_probe_resolved", False)):
        return

    metadata = getattr(config, "_run_metadata", None)
    if not isinstance(metadata, dict):
        return

    existing_probe = metadata.get("environment_probe")
    if _probe_is_resolved(existing_probe):
        config._environment_probe_resolved = True
        return

    run_artifacts = getattr(config, "_run_artifacts", None)
    metadata_path = None
    if isinstance(run_artifacts, RunArtifacts):
        metadata_path = run_artifacts.root / "run-metadata.json"

    if metadata_path is not None:
        persisted_metadata = _read_run_metadata_file(metadata_path)
        persisted_probe = persisted_metadata.get("environment_probe") if isinstance(persisted_metadata, dict) else None
        if _probe_is_resolved(persisted_probe):
            config._run_metadata = persisted_metadata
            config._environment_probe_resolved = True
            return

    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return

    probe_base_url, source = _resolve_probe_base_url_from_runtime_items(items)
    if not probe_base_url:
        probe_base_url, source = _resolve_probe_base_url_from_items(config, items)
    if probe_base_url:
        probe = _capture_environment_probe(probe_base_url, env.ignore_https_errors)
        probe["source"] = source
    else:
        probe = {
            "request_url": "",
            "method": "GET",
            "status_code": None,
            "final_url": "",
            "headers": {},
            "captured_at_utc": _utc_now(),
            "error": source,
            "source": source,
        }

    metadata["environment_probe"] = probe
    config._run_metadata = metadata

    probe_resolved = _probe_is_resolved(probe)
    if probe_resolved and isinstance(run_artifacts, RunArtifacts):
        if _is_xdist_worker(config):
            _write_worker_environment_probe_file(run_artifacts, _current_worker_id(), probe)
        else:
            _write_run_metadata_file(run_artifacts, metadata)

    config._environment_probe_resolved = probe_resolved


def _persist_environment_probe(config: pytest.Config, probe: dict[str, Any], source: str) -> bool:
    payload = dict(probe)
    payload["source"] = source
    if not _probe_is_resolved(payload):
        return False

    metadata = getattr(config, "_run_metadata", None)
    if not isinstance(metadata, dict):
        return False

    metadata["environment_probe"] = payload
    config._run_metadata = metadata
    config._environment_probe_resolved = True

    run_artifacts = getattr(config, "_run_artifacts", None)
    if isinstance(run_artifacts, RunArtifacts):
        if _is_xdist_worker(config):
            _write_worker_environment_probe_file(run_artifacts, _current_worker_id(), payload)
        else:
            _write_run_metadata_file(run_artifacts, metadata)
    return True


def _write_run_metadata_file(artifacts: RunArtifacts, metadata: dict[str, Any]) -> None:
    payload = dict(metadata) if isinstance(metadata, dict) else {}
    payload["tester"] = str(payload.get("tester", "") or "")
    payload["run_note"] = str(payload.get("run_note", "") or "")
    target_git_info = payload.get("target_git_info")
    if not isinstance(target_git_info, dict):
        target_git_info = _default_target_git_info()
    for target in ("frontend", "backend"):
        target_payload = target_git_info.get(target)
        if not isinstance(target_payload, dict):
            target_payload = {}
        endpoint_default = "/git-info"
        target_git_info[target] = {
            "branch": str(target_payload.get("branch", "") or ""),
            "commit": str(target_payload.get("commit", "") or ""),
            "endpoint": str(target_payload.get("endpoint", endpoint_default) or endpoint_default),
            "url": str(target_payload.get("url", "") or ""),
            "status": str(target_payload.get("status", "not_configured") or "not_configured"),
            "error": str(target_payload.get("error", "") or ""),
            "fetched_at_utc": str(target_payload.get("fetched_at_utc", _utc_now()) or _utc_now()),
        }
    payload["target_git_info"] = target_git_info
    target = artifacts.root / "run-metadata.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.parent / f"{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _replace_with_retry(temp, target)


def _read_run_metadata_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    target_git_info = payload.get("target_git_info")
    if not isinstance(target_git_info, dict):
        payload["target_git_info"] = _default_target_git_info()
    return dict(payload)


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
    metadata: dict[str, Any],
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


def _resolve_execution_context(env: RuntimeEnv, browser_session: object | None = None) -> dict[str, object]:
    session = browser_session if isinstance(browser_session, BrowserSession) else None
    if session is None:
        return {
            "browser": env.browser,
            "headless": env.headless,
            "grid_enabled": env.is_grid_available,
            "grid_provider": env.grid_provider if env.is_grid_available else "",
            "grid_endpoint": env.grid_ws_endpoint if env.is_grid_available else "",
            "grid_cdp_endpoint": env.grid_cdp_endpoint if env.is_grid_available else "",
        }

    grid_enabled = session.provider != "local"
    grid_endpoint = ""
    grid_cdp_endpoint = ""
    if session.provider == "playwright":
        grid_endpoint = session.endpoint
    elif session.provider == "selenium_cdp":
        grid_endpoint = session.selenium_grid_url
        grid_cdp_endpoint = session.endpoint

    return {
        "browser": env.browser,
        "headless": env.headless,
        "grid_enabled": grid_enabled,
        "grid_provider": session.provider if grid_enabled else "",
        "grid_endpoint": grid_endpoint,
        "grid_cdp_endpoint": grid_cdp_endpoint,
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
    _replace_with_retry(temp, target)


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
    _refresh_environment_probe_metadata(config, items)

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


def pytest_collection_finish(session: pytest.Session) -> None:
    items = list(getattr(session, "items", []) or [])
    _refresh_environment_probe_metadata(session.config, items)


@pytest.fixture(scope="session", autouse=True)
def _capture_environment_probe_from_runtime_env(
    runtime_env: RuntimeEnv,
    pytestconfig: pytest.Config,
) -> None:
    if bool(getattr(pytestconfig, "_environment_probe_resolved", False)):
        return
    base_url = str(getattr(runtime_env, "base_url", "") or "").strip()
    if not base_url:
        return
    probe = _capture_environment_probe(base_url, runtime_env.ignore_https_errors)
    _persist_environment_probe(pytestconfig, probe, "runtime_env_fixture")


def pytest_configure(config: pytest.Config) -> None:
    _assert_supported_plugin_profile(config)
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
    metadata_path = artifacts.root / "run-metadata.json"
    if _is_xdist_worker(config):
        persisted_metadata = _read_run_metadata_file(metadata_path)
        if isinstance(persisted_metadata, dict):
            run_metadata = persisted_metadata
    else:
        initial_probe = _capture_environment_probe(env.base_url, env.ignore_https_errors)
        initial_probe["source"] = "runtime_env.base_url"
        target_git_info = _capture_target_git_info(env)
        run_metadata = {
            **run_metadata,
            "environment_probe": initial_probe,
            "target_git_info": target_git_info,
        }
    config._run_metadata = run_metadata
    config._environment_probe_resolved = _probe_is_resolved(run_metadata.get("environment_probe"))
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
            **_resolve_execution_context(env),
            "viewport": str(getattr(session.config.option, "viewport", "fhd") or "fhd"),
            "profile": _resolve_run_profile(session.config),
        },
        "target": {
            "server_name": env.server_name,
            "base_url": env.base_url,
            "environment_probe": session.config._run_metadata.get("environment_probe", {}),
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

    _refresh_environment_probe_metadata(item.config, [item])

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
        "execution": _resolve_execution_context(env, getattr(item.config, "_browser_session", None)),
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
