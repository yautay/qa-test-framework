from __future__ import annotations

from pathlib import Path

import pytest

from framework.env import RuntimeEnv
from framework.visual.models import VisualScenario
from framework.visual.runner import VisualRunner
from framework.visual.scenario_loader import load_scenarios_with_errors, format_load_errors


def _repo_root_from(test_file: Path) -> Path:
    resolved = test_file.resolve()
    for parent in resolved.parents:
        if parent.name == "qa":
            return parent.parent
    return resolved.parents[-1]


def scenario_params(pytestconfig: pytest.Config, scenarios_dir: Path) -> list[VisualScenario]:
    scenarios, errors = load_scenarios_with_errors(scenarios_dir)
    if errors:
        raise pytest.UsageError(format_load_errors(errors))
    return scenarios


def viewport_params(pytestconfig: pytest.Config) -> list[str]:
    return [str(pytestconfig.getoption("viewport"))]


def apply_parametrization(metafunc: pytest.Metafunc, scenarios_dir: Path) -> None:
    if "scenario" not in metafunc.fixturenames:
        return
    scenarios = scenario_params(metafunc.config, scenarios_dir=scenarios_dir)
    viewports = viewport_params(metafunc.config)
    params: list[tuple[VisualScenario, str]] = []
    ids: list[str] = []
    for scenario in scenarios:
        if scenario.viewport:
            for viewport in scenario.viewport:
                params.append((scenario, viewport))
                ids.append(f"{scenario.scenario_id}__{viewport}")
        else:
            for viewport in viewports:
                params.append((scenario, viewport))
                ids.append(f"{scenario.scenario_id}__{viewport}")
    metafunc.parametrize("scenario,viewport", params, ids=ids)


def execute_visual_scenario(
        *,
        request: pytest.FixtureRequest,
        page,
        scenario: VisualScenario,
        viewport: str,
        runtime_env: RuntimeEnv,
        visual_output_dir: Path,
        visual_results: list,
        pytestconfig: pytest.Config,
) -> None:
    if not runtime_env.base_url and not scenario.target_url.startswith(("http://", "https://")):
        pytest.skip("BASE_URL is not configured for relative visual target_url")

    runner = VisualRunner(runtime_env, _repo_root_from(Path(__file__)), visual_output_dir)
    result = runner.run(page, scenario, viewport=viewport)

    visual_results.append(result)
    request.node._artifacts_payload = {
        "visual_baseline": result.baseline_path,
        "visual_actual": result.actual_path,
        "visual_diff": result.diff_path,
        "visual_heatmap": result.heatmap_path,
    }
    request.node._visual_payload = {
        "threshold_scope": "scenario+viewport+browser",
        "thresholds_used": {
            "pixel_max": result.thresholds.pixel_max,
            "lpips_max": result.thresholds.lpips_max,
            "dists_max": result.thresholds.dists_max,
        },
        "scores": {
            "pixel_changed_ratio": result.pixel_changed_ratio,
            "lpips": result.lpips,
            "dists": result.dists,
        },
        "verdict": result.status,
    }

    if result.status == "approved":
        return
    if result.status == "warn" and not runtime_env.visual_warn_as_fail:
        return
    if result.status in {"passed", "new"}:
        return
    pytest.fail(result.message)
