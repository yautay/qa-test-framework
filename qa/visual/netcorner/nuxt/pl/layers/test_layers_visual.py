from __future__ import annotations

from pathlib import Path

import pytest

from framework.env import RuntimeEnv
from framework.targeting import resolve_reference_base_url
from framework.visual.models import VisualScenario
from framework.visual.visual_suite import apply_parametrization, execute_visual_scenario
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import valid_client_case

SCENARIOS_DIR = Path(__file__).resolve().parent


pytestmark = [pytest.mark.visual]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    apply_parametrization(metafunc, scenarios_dir=SCENARIOS_DIR)

@pytest.mark.parametrize(
    "user_case",
    valid_client_case(),
    ids=lambda case: case.case_id,
)
def test_layers_visual(
    request: pytest.FixtureRequest,
    page,
    context,
    scenario: VisualScenario,
    viewport: str,
    base_url: str,
    runtime_env: RuntimeEnv,
    visual_output_dir: Path,
    visual_results: list,
    pytestconfig: pytest.Config,
    user_case,
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
    user_data = user_case.factory()
    result = ClientWrappers(page, context, runtime_env).register_new_client(user_data, back_to_hero_page=False)
    assert result, "Użytkownik nie został poprawnie zarejestrowany."