from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from framework.env import load_env
from framework.visual.models import VisualResult, VisualScenario
from framework.visual import visual_suite
from qa.visual.netcorner.nuxt.pl.url_config import resolve_reference_base_url

pytestmark = [pytest.mark.aso]


def _scenario() -> VisualScenario:
    return VisualScenario.from_dict(
        {
            "id": "hero",
            "name": "Hero",
            "target_url": "/",
            "suite_id": "suite-1",
            "compare_mode": "pixel",
            "capture": {"type": "page", "full_page": True},
            "thresholds": {"pixel_max": 0.01, "lpips_max": 0.1, "dists_max": 0.1},
        }
    )


def _make_request(nodeid: str = "qa/visual/test_case.py::test_visual") -> SimpleNamespace:
    return SimpleNamespace(node=SimpleNamespace(nodeid=nodeid))


def _make_pytestconfig(tmp_path: Path) -> SimpleNamespace:
    run_root = tmp_path / "artifacts" / "run-1"
    run_root.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(
        rootpath=tmp_path,
        _run_metadata={"tester": "qa", "run_note": "dual"},
        _run_artifacts=SimpleNamespace(root=run_root, run_id="run-1"),
    )


def test_execute_visual_scenario_uses_dual_pass_when_reference_host_is_set(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, str]] = []

    class FakeRunner:
        def __init__(self, env, repo_root: Path, output_dir: Path) -> None:
            self.env = env
            self.repo_root = repo_root
            self.output_dir = output_dir

        def run(self, page, scenario: VisualScenario, viewport: str) -> VisualResult:
            actual = self.output_dir / "actual" / f"{scenario.scenario_id}__{viewport}.png"
            actual.parent.mkdir(parents=True, exist_ok=True)
            actual.write_bytes(b"png")
            calls.append({"base_url": self.env.base_url, "output_dir": str(self.output_dir)})
            if "reference-pass" in str(self.output_dir):
                return VisualResult(
                    scenario_id=scenario.scenario_id,
                    status="new",
                    message="Baseline missing",
                    compare_mode="pixel",
                    suite_id=scenario.suite_id,
                    viewport=viewport,
                    browser="chromium",
                    baseline_path="",
                    actual_path=str(actual),
                    diff_path="",
                    heatmap_path="",
                    pixel_changed_ratio=1.0,
                    lpips=None,
                    dists=None,
                    thresholds=scenario.thresholds,
                )
            return VisualResult(
                scenario_id=scenario.scenario_id,
                status="passed",
                message="Pixel threshold passed",
                compare_mode="pixel",
                suite_id=scenario.suite_id,
                viewport=viewport,
                browser="chromium",
                baseline_path="/tmp/reference.png",
                actual_path=str(actual),
                diff_path="",
                heatmap_path="",
                pixel_changed_ratio=0.0,
                lpips=None,
                dists=None,
                thresholds=scenario.thresholds,
            )

    monkeypatch.setattr(visual_suite, "VisualRunner", FakeRunner)

    env = load_env()
    env = replace(env, base_url="https://target.example", reference_host="demo")
    request = _make_request()
    pytestconfig = _make_pytestconfig(tmp_path)
    visual_results: list[VisualResult] = []

    visual_suite.execute_visual_scenario(
        request=request,
        page=object(),
        scenario=_scenario(),
        viewport="fhd",
        runtime_env=env,
        visual_output_dir=tmp_path / "visual",
        visual_results=visual_results,
        pytestconfig=pytestconfig,
        resolve_reference_base_url=resolve_reference_base_url,
    )

    assert len(calls) == 2
    assert calls[0]["base_url"] == "https://sklep3-demo.komputronik.dev"
    assert calls[1]["base_url"] == "https://target.example"
    assert len(visual_results) == 1
    assert visual_results[0].test_metadata["execution"]["target_base_url"] == "https://target.example"
    payload = request.node._visual_payload
    assert payload["execution"]["dual_pass"] is True
    assert payload["execution"]["reference_host"] == "demo"
    assert isinstance(payload["execution"]["reference_pass_duration_ms"], int)
    assert isinstance(payload["execution"]["target_pass_duration_ms"], int)
    assert payload["execution"]["pms_requested"] is True
    assert payload["execution"]["pms_configured"] is True
    assert payload["execution"]["pms_usage_state"] == "deferred"
    assert "visual_reference_actual" in request.node._artifacts_payload
    assert "visual_reference_baseline" in request.node._artifacts_payload


def test_execute_visual_scenario_uses_single_pass_when_reference_host_is_empty(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    class FakeRunner:
        def __init__(self, env, repo_root: Path, output_dir: Path) -> None:
            self.env = env
            self.output_dir = output_dir

        def run(self, page, scenario: VisualScenario, viewport: str) -> VisualResult:
            actual = self.output_dir / "actual" / f"{scenario.scenario_id}__{viewport}.png"
            actual.parent.mkdir(parents=True, exist_ok=True)
            actual.write_bytes(b"png")
            calls.append(self.env.base_url)
            return VisualResult(
                scenario_id=scenario.scenario_id,
                status="passed",
                message="Pixel threshold passed",
                compare_mode="pixel",
                suite_id=scenario.suite_id,
                viewport=viewport,
                browser="chromium",
                baseline_path="/tmp/baseline.png",
                actual_path=str(actual),
                diff_path="",
                heatmap_path="",
                pixel_changed_ratio=0.0,
                lpips=None,
                dists=None,
                thresholds=scenario.thresholds,
            )

    monkeypatch.setattr(visual_suite, "VisualRunner", FakeRunner)

    env = load_env()
    env = replace(env, base_url="https://target.example", reference_host="")
    request = _make_request()
    pytestconfig = _make_pytestconfig(tmp_path)
    visual_results: list[VisualResult] = []

    visual_suite.execute_visual_scenario(
        request=request,
        page=object(),
        scenario=_scenario(),
        viewport="fhd",
        runtime_env=env,
        visual_output_dir=tmp_path / "visual",
        visual_results=visual_results,
        pytestconfig=pytestconfig,
    )

    assert calls == ["https://target.example"]
    assert len(visual_results) == 1
    assert visual_results[0].test_metadata["execution"]["target_base_url"] == "https://target.example"
    payload = request.node._visual_payload
    assert payload["execution"]["dual_pass"] is False
    assert payload["execution"]["pms_usage_state"] in {"deferred", "disabled", "not_applicable"}
    assert "visual_reference_actual" not in request.node._artifacts_payload
