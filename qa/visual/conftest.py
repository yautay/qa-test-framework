from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from framework.artifacts import RunArtifacts
from framework.env import RuntimeEnv
from framework.visual.report_builder import write_visual_report

VIEWPORT_PRESETS: dict[str, tuple[int, int]] = {
    "mobile": (390, 844),
    "tablet": (1024, 1366),
    "fhd": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}


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
    results: list = []
    yield results
    report_dir = pytestconfig._run_artifacts.root / "visual-report"
    write_visual_report(report_dir, results)


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
    if "visual_viewport" in request.fixturenames:
        viewport_value = request.getfixturevalue("visual_viewport")
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
