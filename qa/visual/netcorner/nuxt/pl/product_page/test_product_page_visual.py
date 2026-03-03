from __future__ import annotations

from pathlib import Path

import pytest

from framework.env import RuntimeEnv
from framework.visual.models import VisualScenario
from qa.visual.netcorner.nuxt.pl.visual_suite import apply_parametrization, execute_visual_scenario

SCENARIOS_DIR = Path(__file__).resolve().parent

pytestmark = [pytest.mark.visual]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    apply_parametrization(metafunc, scenarios_dir=SCENARIOS_DIR)


def test_product_page_visual(
    request: pytest.FixtureRequest,
    page,
    scenario: VisualScenario,
    viewport: str,
    runtime_env: RuntimeEnv,
    visual_output_dir: Path,
    visual_results: list,
    pytestconfig: pytest.Config,
) -> None:
    execute_visual_scenario(
        request=request,
        page=page,
        scenario=scenario,
        viewport=viewport,
        runtime_env=runtime_env,
        visual_output_dir=visual_output_dir,
        visual_results=visual_results,
        pytestconfig=pytestconfig,
    )
