from __future__ import annotations

from pathlib import Path

import pytest

from framework.env import RuntimeEnv
from framework.targeting import resolve_reference_base_url
from framework.visual.visual_suite import apply_parametrization, execute_visual_scenario
from framework.visual.models import VisualScenario

SCENARIOS_DIR = Path(__file__).resolve().parent

pytestmark = [pytest.mark.visual]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    apply_parametrization(metafunc, scenarios_dir=SCENARIOS_DIR)


def test_listings_visual(
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
