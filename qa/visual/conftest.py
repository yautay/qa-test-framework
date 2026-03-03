from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

import settings
from framework.artifacts import RunArtifacts
from framework.env import RuntimeEnv, load_env
from framework.visual.models import VisualResult
from framework.visual.perceptual import prepare_perceptual_placeholders, run_perceptual_postprocess
from framework.visual.report_builder import write_visual_report, write_visual_results_json

VIEWPORT_PRESETS: dict[str, tuple[int, int]] = settings.visual_viewport_presets


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
            logger.error("perceptual_postprocess_failed", run_id=str(run_artifacts.run_id), error=str(exc))
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
def page(context: BrowserContext, runtime_env: RuntimeEnv) -> Page:
    """Function-scoped Playwright page used by visual scenarios."""
    page = context.new_page()
    _set_consent_cookies(page, runtime_env.base_url)
    yield page
    page.close()
