from __future__ import annotations

"""Load visual regression scenario definitions from JSON files."""

import json
from pathlib import Path

from framework.visual.models import (
    VisualCapture,
    VisualMask,
    VisualScenario,
    VisualStep,
    VisualThresholds,
)


def _as_steps(raw_steps: list[dict]) -> tuple[VisualStep, ...]:
    """Translate raw dicts into typed VisualStep dataclasses."""

    steps: list[VisualStep] = []
    for raw in raw_steps:
        steps.append(
            VisualStep(
                action=str(raw.get("action", "")).strip(),
                selector=str(raw.get("selector", "")).strip(),
                value=str(raw.get("value", "")),
                timeout_ms=int(raw.get("timeout_ms", 5000)),
                url=str(raw.get("url", "")).strip(),
            )
        )
    return tuple(steps)


def _load_scenario(file_path: Path) -> VisualScenario:
    """Deserialize a single JSON file into a VisualScenario instance."""

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    scenario_id = str(payload.get("id") or file_path.stem)
    capture_raw = payload.get("capture", {})
    mask_raw = payload.get("mask", {})
    thresholds_raw = payload.get("thresholds", {})

    return VisualScenario(
        scenario_id=scenario_id,
        name=str(payload.get("name") or scenario_id),
        target_url=str(payload.get("target_url", "")).strip(),
        suite_id=str(payload.get("suite_id", "")).strip(),
        compare_mode=str(payload.get("compare_mode", "hybrid")).strip().lower(),
        capture=VisualCapture(
            capture_type=str(capture_raw.get("type", "page")).strip().lower(),
            selector=str(capture_raw.get("selector", "")).strip(),
            full_page=bool(capture_raw.get("full_page", True)),
        ),
        thresholds=VisualThresholds(
            pixel_max=float(thresholds_raw.get("pixel_max", 0.005)),
            lpips_max=float(thresholds_raw.get("lpips_max", 0.08)),
            dists_max=float(thresholds_raw.get("dists_max", 0.08)),
        ),
        mask=VisualMask(
            selectors=tuple(mask_raw.get("selectors", [])),
            color=str(mask_raw.get("color", "#00FF00")),
        ),
        steps=_as_steps(payload.get("steps", [])),
        perceptual_required=bool(payload.get("perceptual_required", False)),
    )


def load_scenarios(scenarios_dir: Path, scenario_filter: str = "") -> list[VisualScenario]:
    """Load and optionally filter all scenario definitions located under a directory."""

    scenarios: list[VisualScenario] = []
    filter_value = scenario_filter.strip().lower()
    for file_path in sorted(scenarios_dir.glob("*.json")):
        scenario = _load_scenario(file_path)
        if filter_value and filter_value not in scenario.scenario_id.lower():
            continue
        scenarios.append(scenario)
    return scenarios
