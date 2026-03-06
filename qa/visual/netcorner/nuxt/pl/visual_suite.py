from __future__ import annotations

import os
import time
from dataclasses import replace
from pathlib import Path

import pytest
from loguru import logger

from framework.env import RuntimeEnv
from framework.url_resolver.url_resolver import EnvUrls, url_resolver
from framework.visual.baseline_store import BaselineStore
from framework.visual.models import VisualResult, VisualScenario
from framework.visual.runner import VisualRunner
from framework.visual.scenario_loader import format_load_errors, load_scenarios_with_errors

resolve_pl = url_resolver(
    EnvUrls(
        prod="https://komputronik.pl",
        demo="https://sklep3-demo.komputronik.dev",
        test_template="https://komputronik-{host}.netcorner.pl",
        local="https://komputronik.local",
    )
)

_REFERENCE_ENV_ALIASES = {"demo", "prod", "local"}


def _repo_root_from(test_file: Path) -> Path:
    resolved = test_file.resolve()
    for parent in resolved.parents:
        if parent.name == "qa":
            return parent.parent
    return resolved.parents[-1]


def _worker_id() -> str:
    return str(os.getenv("PYTEST_XDIST_WORKER") or "master")


def _resolve_reference_base_url(reference_host: str) -> tuple[str, str, str]:
    token = str(reference_host or "").strip().lower()
    if not token:
        raise ValueError("reference_host is required for reference pass")
    if token in _REFERENCE_ENV_ALIASES:
        return resolve_pl(token).rstrip("/"), token, "reference_alias"
    return resolve_pl(token).rstrip("/"), token, "reference_host"


def _attach_result_metadata(
    *,
    result: VisualResult,
    scenario: VisualScenario,
    viewport: str,
    tester: str,
    run_note: str,
    dual_pass: bool,
    reference_host: str,
    reference_url: str,
    reference_pass_duration_ms: int | None,
    target_pass_duration_ms: int | None,
    dual_pass_total_ms: int | None,
) -> None:
    raw_definition = getattr(scenario, "raw_definition", {})
    if not isinstance(raw_definition, dict):
        raw_definition = {}
    source_file = str(getattr(scenario, "source_file", "") or "")
    result.tester = tester
    result.run_note = run_note
    thresholds = result.thresholds
    result.test_metadata = {
        "run": {
            "tester": tester,
            "run_note": run_note,
        },
        "scenario": {
            "id": scenario.scenario_id,
            "name": scenario.name,
            "suite_id": scenario.suite_id,
            "target_url": scenario.target_url,
            "compare_mode": scenario.compare_mode,
            "viewport": viewport,
            "browser": result.browser,
            "capture": {
                "type": scenario.capture.capture_type,
                "selector": scenario.capture.selector,
                "full_page": scenario.capture.full_page,
            },
            "mask": {
                "selectors": list(scenario.mask.selectors),
                "color": scenario.mask.color,
            },
            "json_source": {
                "file": source_file,
                "definition": raw_definition,
            },
        },
        "scores": {
            "pixel_changed_ratio": result.pixel_changed_ratio,
            "lpips": result.lpips,
            "dists": result.dists,
        },
        "thresholds": {
            "pixel_max": thresholds.pixel_max if thresholds else None,
            "lpips_max": thresholds.lpips_max if thresholds else None,
            "dists_max": thresholds.dists_max if thresholds else None,
        },
        "execution": {
            "dual_pass": dual_pass,
            "reference_host": reference_host,
            "reference_url": reference_url,
            "reference_pass_duration_ms": reference_pass_duration_ms,
            "target_pass_duration_ms": target_pass_duration_ms,
            "dual_pass_total_ms": dual_pass_total_ms,
        },
        "verdict": result.status,
        "message": result.message,
    }


def _finalize_result(
    *,
    request: pytest.FixtureRequest,
    result: VisualResult,
    thresholds,
    visual_results: list,
    dual_pass: bool,
    reference_host: str,
    reference_url: str,
    reference_pass_duration_ms: int | None,
    target_pass_duration_ms: int,
    dual_pass_total_ms: int,
    reference_actual_path: str = "",
    reference_baseline_path: str = "",
) -> None:
    visual_results.append(result)
    artifacts_payload = {
        "visual_baseline": result.baseline_path,
        "visual_actual": result.actual_path,
        "visual_diff": result.diff_path,
        "visual_heatmap": result.heatmap_path,
    }
    if reference_actual_path:
        artifacts_payload["visual_reference_actual"] = reference_actual_path
    if reference_baseline_path:
        artifacts_payload["visual_reference_baseline"] = reference_baseline_path
    request.node._artifacts_payload = artifacts_payload
    request.node._visual_payload = {
        "threshold_scope": "scenario+viewport+browser",
        "thresholds_used": {
            "pixel_max": thresholds.pixel_max if thresholds else None,
            "lpips_max": thresholds.lpips_max if thresholds else None,
            "dists_max": thresholds.dists_max if thresholds else None,
        },
        "scores": {
            "pixel_changed_ratio": result.pixel_changed_ratio,
            "lpips": result.lpips,
            "dists": result.dists,
        },
        "execution": {
            "dual_pass": dual_pass,
            "reference_host": reference_host,
            "reference_url": reference_url,
            "reference_pass_duration_ms": reference_pass_duration_ms,
            "target_pass_duration_ms": target_pass_duration_ms,
            "dual_pass_total_ms": dual_pass_total_ms,
        },
        "verdict": result.status,
    }


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

    repo_root = _repo_root_from(Path(__file__))
    run_metadata = getattr(pytestconfig, "_run_metadata", {})
    tester = ""
    run_note = ""
    if isinstance(run_metadata, dict):
        tester = str(run_metadata.get("tester", "") or "")
        run_note = str(run_metadata.get("run_note", "") or "")

    reference_host = str(getattr(runtime_env, "reference_host", "") or "").strip()
    worker_id = _worker_id()
    run_id = str(getattr(getattr(pytestconfig, "_run_artifacts", None), "run_id", "") or "")

    if not reference_host:
        logger.info(
            "visual_dual_pass_disabled",
            nodeid=request.node.nodeid,
            run_id=run_id,
            scenario_id=scenario.scenario_id,
            suite_id=scenario.suite_id,
            viewport=viewport,
            worker_id=worker_id,
        )
        runner = VisualRunner(runtime_env, repo_root, visual_output_dir)
        target_pass_started = time.perf_counter()
        result = runner.run(page, scenario, viewport=viewport)
        target_pass_duration_ms = int((time.perf_counter() - target_pass_started) * 1000)
        _attach_result_metadata(
            result=result,
            scenario=scenario,
            viewport=viewport,
            tester=tester,
            run_note=run_note,
            dual_pass=False,
            reference_host="",
            reference_url="",
            reference_pass_duration_ms=None,
            target_pass_duration_ms=target_pass_duration_ms,
            dual_pass_total_ms=target_pass_duration_ms,
        )
        thresholds = result.thresholds
        _finalize_result(
            request=request,
            result=result,
            thresholds=thresholds,
            visual_results=visual_results,
            dual_pass=False,
            reference_host="",
            reference_url="",
            reference_pass_duration_ms=None,
            target_pass_duration_ms=target_pass_duration_ms,
            dual_pass_total_ms=target_pass_duration_ms,
        )
    else:
        logger.info(
            "visual_dual_pass_enabled",
            nodeid=request.node.nodeid,
            run_id=run_id,
            scenario_id=scenario.scenario_id,
            suite_id=scenario.suite_id,
            viewport=viewport,
            reference_host=reference_host,
            worker_id=worker_id,
        )
        try:
            reference_url, _, reference_source = _resolve_reference_base_url(reference_host)
        except ValueError as exc:
            logger.error(
                "visual_reference_resolve_failed",
                nodeid=request.node.nodeid,
                scenario_id=scenario.scenario_id,
                viewport=viewport,
                reference_host=reference_host,
                error=str(exc),
            )
            pytest.fail(f"reference_host resolve failed: {exc}")
            return

        logger.info(
            "runtime_reference_resolved",
            nodeid=request.node.nodeid,
            scenario_id=scenario.scenario_id,
            viewport=viewport,
            reference_host=reference_host,
            reference_url=reference_url,
            source=reference_source,
        )

        run_artifacts = getattr(pytestconfig, "_run_artifacts", None)
        run_root = Path(getattr(run_artifacts, "root", visual_output_dir.parent))
        reference_root = run_root / "visual" / "reference-pass" / worker_id
        reference_cache_dir = reference_root / "cache"
        reference_output_dir = reference_root / "captures"
        reference_cache_dir.mkdir(parents=True, exist_ok=True)
        reference_output_dir.mkdir(parents=True, exist_ok=True)

        compare_env = replace(
            runtime_env,
            visual_baseline_provider="",
            visual_cache_dir=str(reference_cache_dir),
        )
        reference_env = replace(compare_env, base_url=reference_url)

        dual_started = time.perf_counter()
        logger.info(
            "visual_reference_pass_start",
            nodeid=request.node.nodeid,
            scenario_id=scenario.scenario_id,
            viewport=viewport,
            reference_url=reference_url,
            reference_cache_dir=str(reference_cache_dir),
        )
        reference_pass_started = time.perf_counter()
        reference_runner = VisualRunner(reference_env, repo_root, reference_output_dir)
        reference_result = reference_runner.run(page, scenario, viewport=viewport)
        reference_pass_duration_ms = int((time.perf_counter() - reference_pass_started) * 1000)

        source_actual = Path(reference_result.actual_path)
        if not source_actual.is_file():
            logger.error(
                "visual_reference_pass_failed",
                nodeid=request.node.nodeid,
                scenario_id=scenario.scenario_id,
                viewport=viewport,
                reference_actual_path=reference_result.actual_path,
                message="Reference pass did not produce actual screenshot",
            )
            pytest.fail("Reference pass did not produce actual screenshot")
            return

        store = BaselineStore(compare_env, repo_root)
        stored_baseline = store.store_baseline(
            scenario.suite_id,
            scenario.scenario_id,
            viewport,
            reference_result.browser,
            source_actual,
        )
        logger.info(
            "visual_reference_pass_done",
            nodeid=request.node.nodeid,
            scenario_id=scenario.scenario_id,
            viewport=viewport,
            reference_pass_duration_ms=reference_pass_duration_ms,
            reference_actual_path=reference_result.actual_path,
            stored_baseline_path=str(stored_baseline),
            reference_status=reference_result.status,
        )

        logger.info(
            "visual_target_pass_start",
            nodeid=request.node.nodeid,
            scenario_id=scenario.scenario_id,
            viewport=viewport,
            target_base_url=runtime_env.base_url,
        )
        target_pass_started = time.perf_counter()
        target_runner = VisualRunner(compare_env, repo_root, visual_output_dir)
        result = target_runner.run(page, scenario, viewport=viewport)
        target_pass_duration_ms = int((time.perf_counter() - target_pass_started) * 1000)
        dual_pass_total_ms = int((time.perf_counter() - dual_started) * 1000)
        logger.info(
            "visual_target_pass_done",
            nodeid=request.node.nodeid,
            scenario_id=scenario.scenario_id,
            viewport=viewport,
            target_pass_duration_ms=target_pass_duration_ms,
            dual_pass_total_ms=dual_pass_total_ms,
            status=result.status,
        )

        _attach_result_metadata(
            result=result,
            scenario=scenario,
            viewport=viewport,
            tester=tester,
            run_note=run_note,
            dual_pass=True,
            reference_host=reference_host,
            reference_url=reference_url,
            reference_pass_duration_ms=reference_pass_duration_ms,
            target_pass_duration_ms=target_pass_duration_ms,
            dual_pass_total_ms=dual_pass_total_ms,
        )
        thresholds = result.thresholds
        _finalize_result(
            request=request,
            result=result,
            thresholds=thresholds,
            visual_results=visual_results,
            dual_pass=True,
            reference_host=reference_host,
            reference_url=reference_url,
            reference_pass_duration_ms=reference_pass_duration_ms,
            target_pass_duration_ms=target_pass_duration_ms,
            dual_pass_total_ms=dual_pass_total_ms,
            reference_actual_path=reference_result.actual_path,
            reference_baseline_path=str(stored_baseline),
        )

    return
