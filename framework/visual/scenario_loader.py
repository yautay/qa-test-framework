from __future__ import annotations

"""Load visual regression scenario definitions from JSON files (with error aggregation)."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from framework.visual.models import (
    VisualCapture,
    VisualMask,
    VisualScenario,
    VisualStep,
    VisualThresholds,
)


@dataclass(frozen=True)
class ScenarioLoadError:
    """Represents an error when loading a single scenario file."""
    file: Path
    message: str


def _err(file_path: Path, msg: str) -> ValueError:
    return ValueError(f"{file_path.name}: {msg}")


def _as_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    return str(v)


def _as_bool(v: Any, default: bool, file_path: Path, field: str) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    raise _err(file_path, f"{field} must be a boolean")


def _as_int(v: Any, default: int, file_path: Path, field: str) -> int:
    if v is None:
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    raise _err(file_path, f"{field} must be an int")


def _as_float(v: Any, default: float, file_path: Path, field: str) -> float:
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            pass
    raise _err(file_path, f"{field} must be a number")


def _as_str_list(v: Any, file_path: Path, field: str) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        return v
    raise _err(file_path, f"{field} must be a list of strings")


def _as_steps(raw_steps: Any, file_path: Path) -> tuple[VisualStep, ...]:
    """Translate raw dicts into typed VisualStep dataclasses."""
    if raw_steps is None:
        return ()
    if not isinstance(raw_steps, list) or not all(isinstance(x, dict) for x in raw_steps):
        raise _err(file_path, "steps must be a list of objects")

    steps: list[VisualStep] = []
    for i, raw in enumerate(raw_steps):
        steps.append(
            VisualStep(
                action=_as_str(raw.get("action", "")).strip(),
                selector=_as_str(raw.get("selector", "")).strip(),
                value=_as_str(raw.get("value", "")),
                timeout_ms=_as_int(raw.get("timeout_ms", 5000), 5000, file_path, f"steps[{i}].timeout_ms"),
                url=_as_str(raw.get("url", "")).strip(),
            )
        )
    return tuple(steps)


def _load_scenario(file_path: Path) -> VisualScenario:
    """Deserialize a single JSON file into a VisualScenario instance."""
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise _err(file_path, f"invalid JSON: {e}") from e

    if not isinstance(payload, dict):
        raise _err(file_path, "top-level JSON must be an object")

    scenario_id = _as_str(payload.get("id") or file_path.stem).strip()
    if not scenario_id:
        raise _err(file_path, "id must be non-empty")

    name = _as_str(payload.get("name") or scenario_id).strip()
    suite_id = _as_str(payload.get("suite_id", "")).strip()
    target_url = _as_str(payload.get("target_url", "")).strip()
    if not suite_id:
        raise _err(file_path, "suite_id must be non-empty")
    if not target_url:
        raise _err(file_path, "target_url must be non-empty")

    compare_mode = _as_str(payload.get("compare_mode", "hybrid")).strip().lower()
    if compare_mode not in {"pixel", "perceptual", "hybrid"}:
        raise _err(file_path, f"compare_mode must be pixel|perceptual|hybrid (got {compare_mode!r})")

    capture_raw = payload.get("capture") or {}
    if not isinstance(capture_raw, dict):
        raise _err(file_path, "capture must be an object")

    capture_type = _as_str(capture_raw.get("type", "page")).strip().lower()
    if capture_type not in {"page", "viewport", "element"}:
        raise _err(file_path, f"capture.type must be page|viewport|element (got {capture_type!r})")

    mask_raw = payload.get("mask") or {}
    if not isinstance(mask_raw, dict):
        raise _err(file_path, "mask must be an object")

    thresholds_raw = payload.get("thresholds") or {}
    if not isinstance(thresholds_raw, dict):
        raise _err(file_path, "thresholds must be an object")

    return VisualScenario(
        scenario_id=scenario_id,
        name=name,
        target_url=target_url,
        suite_id=suite_id,
        compare_mode=compare_mode,
        capture=VisualCapture(
            capture_type=capture_type,
            selector=_as_str(capture_raw.get("selector", "")).strip(),
            full_page=_as_bool(capture_raw.get("full_page", True), True, file_path, "capture.full_page"),
        ),
        thresholds=VisualThresholds(
            pixel_max=_as_float(thresholds_raw.get("pixel_max", 0.005), 0.005, file_path, "thresholds.pixel_max"),
            lpips_max=_as_float(thresholds_raw.get("lpips_max", 0.08), 0.08, file_path, "thresholds.lpips_max"),
            dists_max=_as_float(thresholds_raw.get("dists_max", 0.08), 0.08, file_path, "thresholds.dists_max"),
        ),
        mask=VisualMask(
            selectors=tuple(_as_str_list(mask_raw.get("selectors"), file_path, "mask.selectors")),
            color=_as_str(mask_raw.get("color", "#00FF00")),
        ),
        steps=_as_steps(payload.get("steps", []), file_path),
        perceptual_required=_as_bool(payload.get("perceptual_required", False), False, file_path, "perceptual_required"),
    )


def load_scenarios_with_errors(
    scenarios_dir: Path,
    scenario_filter: str = "",
) -> tuple[list[VisualScenario], list[ScenarioLoadError]]:
    """Load scenarios and collect errors instead of raising immediately."""
    scenarios: list[VisualScenario] = []
    errors: list[ScenarioLoadError] = []
    filter_value = scenario_filter.strip().lower()

    for file_path in sorted(scenarios_dir.glob("*.json")):
        try:
            scenario = _load_scenario(file_path)
            if filter_value and filter_value not in scenario.scenario_id.lower():
                continue
            scenarios.append(scenario)
        except Exception as exc:
            errors.append(ScenarioLoadError(file=file_path, message=str(exc)))

    return scenarios, errors


def format_load_errors(errors: list[ScenarioLoadError]) -> str:
    """Pretty-print aggregated scenario load errors."""
    if not errors:
        return ""
    lines = ["Visual scenario load errors:"]
    for e in errors:
        lines.append(f"- {e.file.name}: {e.message}")
    return "\n".join(lines)
