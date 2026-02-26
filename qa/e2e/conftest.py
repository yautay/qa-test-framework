from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from framework.artifacts import RunArtifacts
from framework.env import RuntimeEnv
from framework.screenshot_annotator import annotate_fail_screenshot, extract_selector_from_error
from framework.video_utils import ensure_min_fail_video

VIEWPORT_PRESETS: dict[str, tuple[int, int]] = {
    "mobile": (390, 844),
    "tablet": (1024, 1366),
    "fhd": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    """Session Playwright driver used to launch/connect browsers."""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, runtime_env: RuntimeEnv) -> Browser:
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
) -> BrowserContext:
    """Isolated browser context with viewport, tracing, and fail artifacts."""
    context_started = time.perf_counter()
    viewport_preset = str(pytestconfig.getoption("viewport") or "fhd")
    viewport_width, viewport_height = VIEWPORT_PRESETS.get(viewport_preset, VIEWPORT_PRESETS["fhd"])
    context = browser.new_context(
        viewport={"width": viewport_width, "height": viewport_height},
        ignore_https_errors=runtime_env.ignore_https_errors,
        record_video_dir=str(run_artifacts.videos) if runtime_env.record_video else None,
    )
    context.add_init_script(
        """() => {
            const dismiss = () => {
                const accept = document.querySelector('#onetrust-accept-btn-handler');
                if (accept && typeof accept.click === 'function') {
                    accept.click();
                }

                const sdk = document.querySelector('#onetrust-consent-sdk');
                if (sdk) {
                    sdk.remove();
                }

                const backdrop = document.querySelector('.onetrust-pc-dark-filter');
                if (backdrop) {
                    backdrop.remove();
                }

                if (document.body) {
                    document.body.style.overflow = '';
                }
            };

            dismiss();
            const observer = new MutationObserver(dismiss);
            observer.observe(document.documentElement, { childList: true, subtree: true });
            window.addEventListener('load', dismiss, { once: true });
        }"""
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
    else:
        context.tracing.stop()

    context.close()

    if failed and raw_video_path:
        raw = Path(raw_video_path)
        target = run_artifacts.videos / f"{nodeid_safe}_last{runtime_env.video_min_seconds}s.webm"
        saved = ensure_min_fail_video(raw, target, runtime_env.video_min_seconds)
        artifacts_payload["video"] = str(saved)

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


@pytest.fixture(scope="function")
def page(
    request: pytest.FixtureRequest,
    context: BrowserContext,
    run_artifacts: RunArtifacts,
    runtime_env: RuntimeEnv,
    pytestconfig: pytest.Config,
) -> Page:
    """Page object with optional fail screenshot annotation integration."""
    page = context.new_page()
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
        logger.warning(f"raw screenshot capture failed: {exc}")
        page.close()
        return

    selector = extract_selector_from_error(getattr(request.node.rep_call, "longreprtext", ""))
    box = None
    if selector and runtime_env.highlight_on_fail:
        try:
            box = page.locator(selector).first.bounding_box()
        except Exception as exc:
            logger.warning(f"highlight failed: {exc}")

    normalized_box = None
    if box:
        normalized_box = {
            "x": float(box.get("x", 0.0)),
            "y": float(box.get("y", 0.0)),
            "width": float(box.get("width", 0.0)),
            "height": float(box.get("height", 0.0)),
        }

    git = pytestconfig._git_metadata
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
    page.close()
