from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

import settings
from framework.artifacts import RunArtifacts
from framework.browser import close_browser_session, open_browser_session, set_onetrust_consent_cookies
from framework.env import RuntimeEnv, load_env
from framework.visual.build_metadata import build_visual_build_metadata, write_visual_build_metadata
from framework.visual.models import VisualResult
from framework.visual.perceptual import prepare_perceptual_placeholders, run_perceptual_postprocess
from framework.visual.report_builder import write_visual_report, write_visual_results_json

VIEWPORT_PRESETS: dict[str, tuple[int, int]] = settings.visual_viewport_presets
_VISUAL_RESULT_ARTIFACT_KINDS = {
    "visual_baseline": "baseline_path",
    "visual_actual": "actual_path",
    "visual_diff": "diff_path",
    "visual_heatmap": "heatmap_path",
}


def _is_xdist_worker(config: pytest.Config) -> bool:
    worker_id = str(os.getenv("PYTEST_XDIST_WORKER") or "").strip()
    if worker_id and worker_id != "master":
        return True
    return hasattr(config, "workerinput")


def _worker_results_path(run_artifacts: RunArtifacts, worker_id: str) -> Path:
    return run_artifacts.root / "workers" / worker_id / "visual_results.json"


def _dump_worker_visual_results(run_artifacts: RunArtifacts, worker_id: str, results: list[VisualResult]) -> None:
    target = _worker_results_path(run_artifacts, worker_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"results": [result.to_dict() for result in results]}
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)


def _build_update_visual_payload(result: VisualResult, existing_visual: object) -> dict[str, object]:
    thresholds = getattr(result, "thresholds", None)
    shift_effective = getattr(result, "shift_compensation_y_px_effective", None)
    shift_env_default = getattr(result, "shift_compensation_y_px_env_default", None)
    shift_scenario_override = getattr(result, "shift_compensation_y_px_scenario_override", None)
    shift_source = getattr(result, "shift_compensation_y_px_source", None)
    execution: dict[str, object] = {}
    if isinstance(existing_visual, dict):
        execution_value = existing_visual.get("execution")
        if isinstance(execution_value, dict):
            execution = dict(execution_value)
    execution["shift_compensation_y_px_env_default"] = shift_env_default
    execution["shift_compensation_y_px_scenario_override"] = shift_scenario_override
    execution["shift_compensation_y_px_effective"] = shift_effective
    execution["shift_compensation_y_px_source"] = shift_source
    return {
        "threshold_scope": "scenario+viewport+browser",
        "thresholds_used": {
            "pixel_max": thresholds.pixel_max if thresholds else None,
            "lpips_max": thresholds.lpips_max if thresholds else None,
            "dists_max": thresholds.dists_max if thresholds else None,
            "shift_compensation_y_px": thresholds.shift_compensation_y_px if thresholds else None,
        },
        "scores": {
            "pixel_changed_ratio": result.pixel_changed_ratio,
            "applied_shift_y": result.applied_shift_y,
            "shift_compensation_y_px_effective": shift_effective,
            "lpips": result.lpips,
            "dists": result.dists,
        },
        "execution": execution,
        "verdict": result.status,
    }


def _sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _build_artifact_entry(kind: str, raw_path: str, report_dir: Path | None) -> dict[str, object]:
    path_token = str(raw_path or "").strip()
    available = False
    size_bytes = 0
    size_mib = 0.0
    sha256 = ""
    if path_token:
        artifact_path = Path(path_token)
        if not artifact_path.is_absolute() and report_dir is not None:
            artifact_path = report_dir / artifact_path
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


def _merge_visual_result_artifacts(
    existing_artifacts: object,
    result: VisualResult,
    report_dir: Path | None,
) -> list[dict[str, object]]:
    merged: list[dict[str, object]] = []
    if isinstance(existing_artifacts, list):
        for item in existing_artifacts:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip()
            if kind in _VISUAL_RESULT_ARTIFACT_KINDS:
                continue
            merged.append(dict(item))
    for kind, attr_name in _VISUAL_RESULT_ARTIFACT_KINDS.items():
        merged.append(_build_artifact_entry(kind, str(getattr(result, attr_name, "") or ""), report_dir))
    return merged


def _send_test_result_updates(
    pytestconfig: pytest.Config, run_artifacts: RunArtifacts, results: list[VisualResult]
) -> None:
    reporting_client = getattr(pytestconfig, "_reporting_client", None)
    if reporting_client is None or not bool(getattr(reporting_client, "enabled", False)):
        return

    payloads_by_nodeid = getattr(pytestconfig, "_test_result_payloads", None)
    if not isinstance(payloads_by_nodeid, dict):
        return

    run_uid = str(getattr(pytestconfig, "_run_uid", "") or "")
    if not run_uid:
        return
    run_root = getattr(run_artifacts, "root", None)
    report_dir = run_root / "visual" if isinstance(run_root, Path) else None

    for result in results:
        nodeid = str(getattr(result, "nodeid", "") or "").strip()
        if not nodeid:
            continue
        base_payload = payloads_by_nodeid.get(nodeid)
        if not isinstance(base_payload, dict):
            continue
        base_visual = base_payload.get("visual")
        if not isinstance(base_visual, dict) or str(base_visual.get("verdict", "")).strip().lower() != "analysis":
            continue
        status = str(getattr(result, "status", "") or "").strip().lower()
        if status == "analysis":
            continue

        update = dict(base_payload)
        attempt = 2
        update["event_id"] = str(uuid.uuid4())
        update["event_type"] = "test_result"
        update["event_time_utc"] = datetime.now(UTC).isoformat()
        update["idempotency_key"] = f"test_result:{run_uid}:{nodeid}:{attempt}"
        update["run_id"] = run_artifacts.run_id
        update["run_uid"] = run_uid
        metadata = base_payload.get("metadata")
        metadata_out = dict(metadata) if isinstance(metadata, dict) else {}
        metadata_out["update_reason"] = "pms_postprocess_finalized"
        update["metadata"] = metadata_out
        update["attempt"] = attempt
        update["test_id"] = nodeid
        update["nodeid"] = nodeid
        update["status"] = status
        update["visual"] = _build_update_visual_payload(result, base_visual)
        update["artifacts"] = _merge_visual_result_artifacts(base_payload.get("artifacts"), result, report_dir)

        logger.info("reporting_test_result_update", run_id=run_artifacts.run_id, nodeid=nodeid, status=status)
        reporting_client.test_result(update)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    visual_root = Path(__file__).resolve().parent
    visual_items: list[pytest.Item] = []
    for item in items:
        try:
            item_path = Path(str(item.fspath)).resolve()
        except Exception:
            continue
        if visual_root in item_path.parents:
            visual_items.append(item)

    for item in visual_items:
        item.add_marker(pytest.mark.visual)
    if not config._runtime_env.visual_enabled:
        skip_marker = pytest.mark.skip(reason="visual suite disabled (VISUAL_ENABLED=0)")
        for item in visual_items:
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def visual_results(pytestconfig: pytest.Config) -> list:
    """Collects visual scenario results and writes local report on session end."""
    results: list[VisualResult] = []
    yield results
    run_artifacts: RunArtifacts = pytestconfig._run_artifacts
    if _is_xdist_worker(pytestconfig):
        _dump_worker_visual_results(run_artifacts, os.getenv("PYTEST_XDIST_WORKER", "master"), results)
        return
    report_dir = run_artifacts.root / "visual"
    runtime_env = getattr(pytestconfig, "_runtime_env", None)
    env = runtime_env if isinstance(runtime_env, RuntimeEnv) else load_env()
    prepare_perceptual_placeholders(
        env=env,
        run_id=str(run_artifacts.run_id),
        report_dir=report_dir,
        results=results,
    )
    write_visual_report(report_dir, results)
    payloads_by_nodeid = getattr(pytestconfig, "_test_result_payloads", None)
    if isinstance(payloads_by_nodeid, dict):
        metadata = build_visual_build_metadata(results=results, payloads_by_nodeid=payloads_by_nodeid)
        write_visual_build_metadata(report_dir, metadata)
    if env.pms_enabled:
        try:
            run_perceptual_postprocess(
                env=env,
                run_id=str(run_artifacts.run_id),
                report_dir=report_dir,
                results=results,
                on_results_updated=lambda: write_visual_results_json(report_dir, results),
            )
        except Exception as exc:
            logger.exception("perceptual_postprocess_failed", run_id=str(run_artifacts.run_id), error=str(exc))
        try:
            _send_test_result_updates(pytestconfig, run_artifacts, results)
        except Exception as exc:
            logger.exception("reporting_test_result_updates_failed", run_id=str(run_artifacts.run_id), error=str(exc))
        write_visual_report(report_dir, results)
        if isinstance(payloads_by_nodeid, dict):
            metadata = build_visual_build_metadata(results=results, payloads_by_nodeid=payloads_by_nodeid)
            write_visual_build_metadata(report_dir, metadata)


@pytest.fixture(scope="session")
def visual_output_dir(run_artifacts: RunArtifacts) -> Path:
    """Run-scoped output directory for visual artifacts and reports."""
    path = run_artifacts.root / "visual"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    """Session Playwright driver for visual suite browser lifecycle."""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> Browser:
    """Session browser for visual tests (local launch or remote connect)."""
    session = open_browser_session(playwright_instance, runtime_env)
    yield session.browser
    close_browser_session(session, runtime_env)


@pytest.fixture(scope="function")
def context(
    request: pytest.FixtureRequest,
    browser: Browser,
    runtime_env: RuntimeEnv,
    pytestconfig: pytest.Config,
) -> BrowserContext:
    """Function-scoped browser context with selected visual viewport preset."""
    viewport_preset = str(pytestconfig.getoption("viewport") or "fhd")
    if "viewport" in request.fixturenames:
        viewport_value = request.getfixturevalue("viewport")
        viewport_preset = str(viewport_value or viewport_preset)
    viewport_width, viewport_height = VIEWPORT_PRESETS.get(viewport_preset, VIEWPORT_PRESETS["fhd"])
    context = browser.new_context(
        viewport={"width": viewport_width, "height": viewport_height},
        ignore_https_errors=runtime_env.ignore_https_errors,
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext, base_url: str) -> Page:
    """Function-scoped Playwright page used by visual scenarios."""
    page = context.new_page()
    set_onetrust_consent_cookies(page, base_url)
    yield page
    page.close()
