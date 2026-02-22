from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, cast
import pytest
import settings
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from framework.artifacts import RunArtifacts
from framework.env import RuntimeEnv
from framework.visual.models import VisualResult, VisualThresholds
from framework.visual.report_builder import write_visual_report

VIEWPORT_PRESETS: dict[str, tuple[int, int]] = settings.visual_viewport_presets


def _is_xdist_worker(config: pytest.Config) -> bool:
    return hasattr(config, "workerinput")


def _is_xdist_controller(config: pytest.Config) -> bool:
    return bool(config.pluginmanager.hasplugin("xdist") and not _is_xdist_worker(config))


def _worker_results_path(run_artifacts: RunArtifacts, worker_id: str) -> Path:
    return run_artifacts.root / ".workers" / worker_id / "visual_results.json"


def _dump_worker_visual_results(run_artifacts: RunArtifacts, worker_id: str, results: list[VisualResult]) -> None:
    target = _worker_results_path(run_artifacts, worker_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"results": [result.to_dict() for result in results]}
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)


def _result_from_dict(data: dict) -> VisualResult | None:
    try:
        status_raw = str(data.get("status") or "failed")
        compare_mode_raw = str(data.get("compare_mode") or "pixel")
        if status_raw not in {
            "passed",
            "failed",
            "skipped",
            "new",
            "uncertain",
            "warn",
            "approved",
            "xfailed",
            "xpassed",
        }:
            status_raw = "failed"
        if compare_mode_raw not in {"pixel", "perceptual", "hybrid"}:
            compare_mode_raw = "pixel"

        thresholds_raw = data.get("thresholds") if isinstance(data.get("thresholds"), dict) else None
        thresholds = None
        if thresholds_raw is not None:
            pixel_uncertain_delta = thresholds_raw.get("pixel_uncertain_delta")
            lpips_uncertain_delta = thresholds_raw.get("lpips_uncertain_delta")
            dists_uncertain_delta = thresholds_raw.get("dists_uncertain_delta")
            thresholds = VisualThresholds(
                pixel_max=float(thresholds_raw.get("pixel_max", 0.0)),
                lpips_max=float(thresholds_raw.get("lpips_max", 0.0)),
                dists_max=float(thresholds_raw.get("dists_max", 0.0)),
                pixel_uncertain_delta=float(pixel_uncertain_delta) if pixel_uncertain_delta is not None else None,
                lpips_uncertain_delta=float(lpips_uncertain_delta) if lpips_uncertain_delta is not None else None,
                dists_uncertain_delta=float(dists_uncertain_delta) if dists_uncertain_delta is not None else None,
            )

        pixel_changed_ratio_raw = data.get("pixel_changed_ratio")
        lpips_raw = data.get("lpips")
        dists_raw = data.get("dists")

        return VisualResult(
            scenario_id=str(data.get("scenario_id") or ""),
            status=cast(Any, status_raw),
            message=str(data.get("message") or ""),
            compare_mode=cast(Any, compare_mode_raw),
            baseline_path=str(data.get("baseline_path") or ""),
            actual_path=str(data.get("actual_path") or ""),
            diff_path=str(data.get("diff_path") or ""),
            heatmap_path=str(data.get("heatmap_path") or ""),
            suite_id=str(data.get("suite_id") or ""),
            viewport=str(data.get("viewport") or ""),
            browser=str(data.get("browser") or ""),
            pixel_changed_ratio=float(pixel_changed_ratio_raw) if pixel_changed_ratio_raw is not None else None,
            lpips=float(lpips_raw) if lpips_raw is not None else None,
            dists=float(dists_raw) if dists_raw is not None else None,
            thresholds=thresholds,
            tester=str(data.get("tester") or ""),
            run_note=str(data.get("run_note") or ""),
            test_metadata=data.get("test_metadata") if isinstance(data.get("test_metadata"), dict) else None,
        )
    except (TypeError, ValueError):
        return None


def _load_merged_worker_visual_results(run_artifacts: RunArtifacts) -> list[VisualResult]:
    workers_root = run_artifacts.root / ".workers"
    if not workers_root.is_dir():
        return []

    merged: dict[tuple[str, str, str], VisualResult] = {}
    for path in sorted(workers_root.glob("*/visual_results.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        rows = payload.get("results", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            result = _result_from_dict(row)
            if result is None:
                continue
            key = (result.scenario_id, result.viewport, result.browser)
            merged[key] = result
    return list(merged.values())


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
    write_visual_report(report_dir, results)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _ = exitstatus
    if not _is_xdist_controller(session.config):
        return

    run_artifacts: RunArtifacts = session.config._run_artifacts
    merged_results = _load_merged_worker_visual_results(run_artifacts)
    if not merged_results:
        return
    report_dir = run_artifacts.root / "visual"
    write_visual_report(report_dir, merged_results)


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
    if runtime_env.is_grid_available:
        browser_name = "chromium" if runtime_env.browser == "chrome" else runtime_env.browser
        browser_type = getattr(playwright_instance, browser_name)
        browser = browser_type.connect(
            runtime_env.grid_ws_endpoint,
            timeout=runtime_env.grid_connect_timeout_ms,
        )
    elif runtime_env.browser == "chrome":
        browser = playwright_instance.chromium.launch(channel="chrome", headless=runtime_env.headless)
    else:
        browser_type = getattr(playwright_instance, runtime_env.browser)
        browser = browser_type.launch(headless=runtime_env.headless)
    yield browser
    browser.close()


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
def page(context: BrowserContext) -> Page:
    """Function-scoped Playwright page used by visual scenarios."""
    page = context.new_page()
    yield page
    page.close()
