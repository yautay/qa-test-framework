from __future__ import annotations

from pathlib import Path

import pytest

from framework.env import RuntimeEnv
from framework.targeting import resolve_reference_base_url
from framework.visual.models import VisualScenario
from framework.visual.visual_suite import apply_parametrization, execute_visual_scenario
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage

SCENARIOS_DIR = Path(__file__).resolve().parent


pytestmark = [pytest.mark.visual]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    apply_parametrization(metafunc, scenarios_dir=SCENARIOS_DIR)

def test_layers_visual(
    request: pytest.FixtureRequest,
    page,
    scenario: VisualScenario,
    viewport: str,
    base_url: str,
    runtime_env: RuntimeEnv,
    visual_output_dir: Path,
    visual_results: list,
    pytestconfig: pytest.Config,
) -> None:
    if scenario.scenario_id == "vrt-netcorner-nuxt-pl-layers-register":
        home = HomePage(page, base_url)
        home.open().wait_loaded().open_register_page()

    execute_visual_scenario(
        request=request,
        page=page,
        scenario=scenario,
        viewport=viewport,
        runtime_env=runtime_env,
        base_url=base_url,
        visual_output_dir=visual_output_dir,
        visual_results=visual_results,
        pytestconfig=pytestconfig,
        resolve_reference_base_url=resolve_reference_base_url,
    )
