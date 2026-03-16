from __future__ import annotations

import importlib
import os
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

try:
    allure = importlib.import_module("allure")
except Exception:  # pragma: no cover - optional dependency
    allure = None

from framework.artifacts import RunArtifacts, resolve_artifacts_base_dir
from framework.env import RuntimeEnv, load_env
from framework.screenshot_annotator import annotate_fail_screenshot, extract_selector_from_error
from framework.video_utils import ensure_min_fail_video

VIEWPORT_PRESETS: dict[str, tuple[int, int]] = {
    "mobile": (390, 844),
    "tablet": (1024, 1366),
    "fhd": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}


def _allure_enabled(pytestconfig: pytest.Config) -> bool:
    if not bool(getattr(pytestconfig, "_allure_enabled", True)):
        return False
    if allure is None:
        return False
    allure_dir = ""
    try:
        allure_dir = str(pytestconfig.getoption("--alluredir") or "")
    except Exception:
        allure_dir = str(getattr(pytestconfig.option, "allure_report_dir", "") or "")
    return bool(allure_dir.strip())


def _resolve_allure_run_id(config: pytest.Config) -> str:
    worker_input = cast(Any, getattr(config, "workerinput", None))
    if isinstance(worker_input, dict):
        worker_run_id = str(worker_input.get("run_id") or "").strip()
        if worker_run_id:
            return worker_run_id

    shared_run_id = str(getattr(config, "_shared_run_id", "") or "").strip()
    if shared_run_id:
        return shared_run_id

    env_run_id = str(os.getenv("PYTEST_XDIST_TESTRUNUID") or "").strip()
    if env_run_id:
        return env_run_id

    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")


def _resolve_report_toggles(config: pytest.Config, env: RuntimeEnv) -> tuple[bool, bool]:
    cli_allure_enabled = getattr(config.option, "allure_enabled", None)
    cli_pytest_html_enabled = getattr(config.option, "pytest_html_enabled", None)
    allure_enabled = env.allure_enabled if cli_allure_enabled is None else bool(cli_allure_enabled)
    pytest_html_enabled = env.pytest_html_enabled if cli_pytest_html_enabled is None else bool(cli_pytest_html_enabled)
    return allure_enabled, pytest_html_enabled


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    run_id = _resolve_allure_run_id(config)
    cast(Any, config)._shared_run_id = run_id
    os.environ.setdefault("PYTEST_XDIST_TESTRUNUID", run_id)

    env = load_env()
    allure_enabled, pytest_html_enabled = _resolve_report_toggles(config, env)
    cast(Any, config)._allure_enabled = allure_enabled
    cast(Any, config)._pytest_html_enabled = pytest_html_enabled

    artifacts_base = resolve_artifacts_base_dir(env.artifacts_dir, config.rootpath)
    run_root = (artifacts_base / run_id).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    current_allure_dir = str(getattr(config.option, "allure_report_dir", "") or "").strip()
    if hasattr(config.option, "allure_report_dir") and allure_enabled and allure is not None and not current_allure_dir:
        allure_results_dir = run_root / "allure-results"
        allure_results_dir.mkdir(parents=True, exist_ok=True)
        cast(Any, config.option).allure_report_dir = str(allure_results_dir)
    if hasattr(config.option, "allure_report_dir") and not allure_enabled:
        cast(Any, config.option).allure_report_dir = ""

    current_html_path = str(getattr(config.option, "htmlpath", "") or "").strip()
    if hasattr(config.option, "htmlpath") and pytest_html_enabled and not current_html_path:
        cast(Any, config.option).htmlpath = str(run_root / "pytest-report.html")
        cast(Any, config.option).self_contained_html = True
    if hasattr(config.option, "htmlpath") and not pytest_html_enabled:
        cast(Any, config.option).htmlpath = ""


def _allure_attach_file(
    pytestconfig: pytest.Config,
    file_path: Path,
    *,
    name: str,
    attachment_type: str,
    extension: str,
) -> None:
    if not _allure_enabled(pytestconfig):
        return
    if not file_path.is_file():
        return
    allure_runtime = cast(Any, allure)
    try:
        allure_runtime.attach.file(
            str(file_path),
            name=name,
            attachment_type=attachment_type,
            extension=extension,
        )
    except Exception as exc:
        logger.debug(
            "allure_attach_skipped",
            file_path=str(file_path),
            attachment_name=name,
            attachment_type=attachment_type,
            extension=extension,
            error=str(exc),
        )


def _allure_apply_dynamic_metadata(
    request: pytest.FixtureRequest,
    runtime_env: RuntimeEnv,
    pytestconfig: pytest.Config,
) -> None:
    if not _allure_enabled(pytestconfig):
        return
    allure_runtime = cast(Any, allure)
    scenario_marker = request.node.get_closest_marker("scenario")
    if scenario_marker and scenario_marker.args:
        scenario_text = str(scenario_marker.args[0]).strip()
        if scenario_text:
            allure_runtime.dynamic.story(scenario_text)
    allure_runtime.dynamic.tag("e2e")
    allure_runtime.dynamic.parameter("browser", runtime_env.browser)
    allure_runtime.dynamic.parameter("viewport", str(pytestconfig.getoption("viewport") or "fhd"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(scope="session")
def playwright_instance() -> Iterator[Playwright]:
    """Session Playwright driver used to launch/connect browsers."""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> Iterator[Browser]:
    """Session browser instance (local launch or remote grid connect)."""
    if runtime_env.is_grid_available:
        if not runtime_env.grid_ws_endpoint:
            raise RuntimeError("is_grid_available is enabled but GRID_WS_ENDPOINT is empty")
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
    run_artifacts: RunArtifacts,
    pytestconfig: pytest.Config,
) -> Iterator[BrowserContext]:
    """Isolated browser context with viewport, tracing, and fail artifacts."""
    context_started = time.perf_counter()
    viewport_preset = str(pytestconfig.getoption("viewport") or "fhd")
    viewport_width, viewport_height = VIEWPORT_PRESETS.get(viewport_preset, VIEWPORT_PRESETS["fhd"])
    context = browser.new_context(
        viewport={"width": viewport_width, "height": viewport_height},
        ignore_https_errors=runtime_env.ignore_https_errors,
        record_video_dir=str(run_artifacts.videos) if runtime_env.record_video else None,
    )
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context

    failed = bool(getattr(request.node, "rep_call", None) and request.node.rep_call.failed)
    nodeid_safe = request.node.nodeid.replace("::", "__").replace("/", "_")
    artifacts_payload: dict[str, str] = {}

    page: Page | None = getattr(request.node, "_page", None)
    raw_video_path: str | None = None
    if page and page.video:
        try:
            raw_video_path = str(page.video.path())
        except Exception:
            raw_video_path = None

    if failed:
        trace_path = run_artifacts.traces / f"{nodeid_safe}.zip"
        context.tracing.stop(path=str(trace_path))
        artifacts_payload["trace"] = str(trace_path)
        _allure_attach_file(
            pytestconfig,
            trace_path,
            name="trace",
            attachment_type="application/zip",
            extension="zip",
        )
    else:
        context.tracing.stop()

    context.close()

    if failed and raw_video_path:
        raw = Path(raw_video_path)
        target = run_artifacts.videos / f"{nodeid_safe}_last{runtime_env.video_min_seconds}s.webm"
        saved = ensure_min_fail_video(raw, target, runtime_env.video_min_seconds)
        artifacts_payload["video"] = str(saved)
        _allure_attach_file(
            pytestconfig,
            saved,
            name="video",
            attachment_type="video/webm",
            extension="webm",
        )

    screenshot_artifacts = getattr(request.node, "_screenshot_artifacts", None)
    if isinstance(screenshot_artifacts, dict):
        artifacts_payload.update(screenshot_artifacts)

    context_duration_seconds = round(time.perf_counter() - context_started, 3)
    logger.info(
        "context_timing",
        nodeid=request.node.nodeid,
        duration_seconds=context_duration_seconds,
        failed=failed,
    )

    if failed:
        request.node._artifacts_payload = artifacts_payload
    else:
        request.node._artifacts_payload = artifacts_payload


def _set_consent_cookies(page: Page, base_url: str) -> None:
    """Set consent cookies to bypass OneTrust banner."""
    if not base_url:
        return
    try:
        hostname = base_url.split("//")[-1].split("/")[0]
        parts = hostname.split(".")
        if len(parts) >= 2:
            domain = "." + ".".join(parts[-2:])
        else:
            domain = hostname
        context = page.context
        context.add_cookies(
            [
                {
                    "name": "OptanonConsent",
                    "value": "data=boBLJIDePN7tABBJRG7LEtAAAAyAABAyAEAQAkABgAGAAYABgAGwAcwBzAG8AdwBuAGMALQA1"
                    "ADgANwA3ADkAOAAxADkAMgA0ADkAMgAzADkAMgAwADkAMgA0ADkAMgA0ADkAOAA1ADkANgA0ADkANgA1"
                    "ADkAMQA3ADkAMQA2ADkAMgA1ADkANgA2ADkANgA3ADkANgA3ADkANgA3ADkAOAA2ADkANgA3ADkANgA4"
                    "ADkANgA4ADkANgA5ADkANgA5ADkANgA5ADkAOAA2ADkANgA5ADkAOAA2ADkANgA3ADkANgA4ADkAOAA3"
                    "ADkAOAA4ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkA,groups=BO_7"
                    ",ACKN_1,AL_1,TE_1,AE_1,ME_1,CU_1,VA_1,PR_1,UA_1,MEPS_1,PV_1,GE_1,SP_1,EM_1,BF_1,WA_1"
                    ",WG_1,OUBO_1,RG_1,OO_1,GR_1,PL_1,CD_1,CO_1,CRT_1,HR_1,PR_1,VO_1,NL_1,OA_1,P_1,PI_1"
                    ",EV_1,AN_1,AO_1,CI_1,CT_1,C_1,DP_1,D_1,ET_1,F_1,IP_1,J_1,K_1,L_1,M_1,N_1,O_1,P_1"
                    ",PM_1,Q_1,R_1,S_1,SF_1,SI_1,SK_1,T_1,U_1,UR_1,VM_1,VT_1,WA_1",
                    "domain": domain,
                    "path": "/",
                },
                {
                    "name": "OptanonAlertBoxClosed",
                    "value": "2024-01-01T00:00:00.000Z",
                    "domain": domain,
                    "path": "/",
                },
            ]
        )
    except Exception:
        pass


@pytest.fixture(scope="function")
def page(
    request: pytest.FixtureRequest,
    context: BrowserContext,
    run_artifacts: RunArtifacts,
    runtime_env: RuntimeEnv,
    pytestconfig: pytest.Config,
) -> Iterator[Page]:
    """Page object with optional fail screenshot annotation integration."""
    _allure_apply_dynamic_metadata(request, runtime_env, pytestconfig)
    page = context.new_page()
    _set_consent_cookies(page, runtime_env.base_url)
    request.node._page = page
    yield page

    failed = bool(getattr(request.node, "rep_call", None) and request.node.rep_call.failed)
    if not failed:
        page.close()
        return

    nodeid_safe = request.node.nodeid.replace("::", "__").replace("/", "_")
    raw_path = run_artifacts.screenshots / f"{nodeid_safe}_raw.png"
    ann_path = run_artifacts.screenshots / f"{nodeid_safe}_annotated.png"
    try:
        page.screenshot(path=str(raw_path), full_page=True)
    except Exception as exc:
        logger.warning(
            "raw_screenshot_capture_failed",
            nodeid=request.node.nodeid,
            path=str(raw_path),
            error=str(exc),
        )
        page.close()
        return

    selector = extract_selector_from_error(getattr(request.node.rep_call, "longreprtext", ""))
    box = None
    if selector and runtime_env.highlight_on_fail:
        try:
            box = page.locator(selector).first.bounding_box()
        except Exception as exc:
            logger.warning(
                "screenshot_highlight_failed",
                nodeid=request.node.nodeid,
                selector=selector,
                error=str(exc),
            )

    normalized_box = None
    if box:
        normalized_box = {
            "x": float(box.get("x", 0.0)),
            "y": float(box.get("y", 0.0)),
            "width": float(box.get("width", 0.0)),
            "height": float(box.get("height", 0.0)),
        }

    git = cast(Any, pytestconfig)._git_metadata
    annotate_fail_screenshot(
        raw_path,
        ann_path,
        {
            "nodeid": request.node.nodeid,
            "branch": git.branch or "",
            "commit": git.commit or "",
            "user": git.user or os.getenv("USER", ""),
        },
        normalized_box,
    )
    request.node._screenshot_artifacts = {
        "screenshot_raw": str(raw_path),
        "screenshot_annotated": str(ann_path),
    }
    _allure_attach_file(
        pytestconfig,
        raw_path,
        name="screenshot_raw",
        attachment_type="image/png",
        extension="png",
    )
    _allure_attach_file(
        pytestconfig,
        ann_path,
        name="screenshot_annotated",
        attachment_type="image/png",
        extension="png",
    )
    page.close()
