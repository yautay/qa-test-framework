from __future__ import annotations

"""Data models that describe visual scenarios, captures, and comparison results.

Includes helpers to load VisualScenario definitions from JSON using the schema:
- scenario id field: "id"
- capture fields: {"type": "page|viewport|element", "full_page": bool, "locator": str}
"""

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

CaptureType = Literal["page", "viewport", "element"]
CompareMode = Literal["pixel", "hybrid"]
ResultStatus = Literal["passed", "failed", "skipped", "new", "uncertain", "analysis"]
DEFAULT_MASK_COLOR = "#DDF527"


def _require_str(d: dict[str, Any], key: str) -> str:
    """
    Return a required non-empty string field from a dictionary.

    Parameters
    ----------
    d : dict[str, Any]
        Source dictionary (typically parsed JSON/config payload).
    key : str
        Field name to read.

    Returns
    -------
    str
        Validated non-empty string value.

    Raises
    ------
    ValueError
        If the field is missing, not a string, or an empty/whitespace value.

    Notes
    -----
    This helper enforces strict schema validation for required
    string fields.
    """

    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"Missing/invalid string field: {key}")
    return v


def _opt_str(d: dict[str, Any], key: str, default: str = "") -> str:
    """
    Return an optional string field from a dictionary.

    Parameters
    ----------
    d : dict[str, Any]
        Source dictionary.
    key : str
        Field name to read.
    default : str, optional
        Value returned when the field is missing or None.

    Returns
    -------
    str
        Field value converted to string, or default.

    Notes
    -----
    - None values resolve to `default`.
    - Non-string values are converted using `str(...)`.
    - Intended for permissive parsing of optional fields.
    """

    v = d.get(key, default)
    if v is None:
        return default
    return str(v)


def _opt_bool(d: dict[str, Any], key: str, default: bool) -> bool:
    """
    Return an optional boolean field from a dictionary.

    Parameters
    ----------
    d : dict[str, Any]
        Source dictionary.
    key : str
        Field name to read.
    default : bool
        Fallback value if the field is missing.

    Returns
    -------
    bool
        Boolean value from the dictionary or default.

    Raises
    ------
    ValueError
        If the value exists but is not a boolean.

    Notes
    -----
    This function performs strict type validation and does not
    coerce values like "true"/"false" strings.
    """

    v = d.get(key, default)
    if isinstance(v, bool):
        return v
    raise ValueError(f"Invalid boolean field: {key}")


def _opt_float(d: dict[str, Any], key: str, default: float) -> float:
    """
    Return an optional numeric field as float.

    Parameters
    ----------
    d : dict[str, Any]
        Source dictionary.
    key : str
        Field name to read.
    default : float
        Fallback value if the field is missing.

    Returns
    -------
    float
        Parsed numeric value converted to float.

    Raises
    ------
    ValueError
        If the value exists but is not int or float.

    Notes
    -----
    Integers are accepted and converted to float.
    No string conversion is performed.
    """

    v = d.get(key, default)
    if isinstance(v, (int, float)):
        return float(v)
    raise ValueError(f"Invalid float field: {key}")


def _opt_int(d: dict[str, Any], key: str, default: int) -> int:
    v = d.get(key, default)
    if isinstance(v, int):
        return int(v)
    raise ValueError(f"Invalid int field: {key}")


def _as_tuple_str(v: Any) -> tuple[str, ...]:
    """
    Normalize a list/tuple of strings into a tuple.

    Parameters
    ----------
    v : Any
        Input value expected to be a list or tuple of strings.

    Returns
    -------
    tuple[str, ...]
        Normalized immutable tuple of strings.

    Raises
    ------
    ValueError
        If the value is not a sequence of strings.

    Notes
    -----
    - None returns an empty tuple.
    - Used to normalize configuration data into immutable form.
    """

    if v is None:
        return ()
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        return tuple(v)
    if isinstance(v, tuple) and all(isinstance(x, str) for x in v):
        return v
    raise ValueError("selectors must be a list of strings")


def _as_tuple_dict(v: Any, field_name: str) -> tuple[dict[str, Any], ...]:
    """
    Normalize a list/tuple of dictionaries into a tuple.

    Parameters
    ----------
    v : Any
        Input value expected to be a list or tuple of dict objects.
    field_name : str
        Field name used for error reporting.

    Returns
    -------
    tuple[dict[str, Any], ...]
        Normalized immutable tuple of dictionaries.

    Raises
    ------
    ValueError
        If the value is not a sequence of dictionaries.

    Notes
    -----
    - None returns an empty tuple.
    - Useful when loading structured configuration sections.
    """

    if v is None:
        return ()
    if isinstance(v, list) and all(isinstance(x, dict) for x in v):
        return tuple(v)
    if isinstance(v, tuple) and all(isinstance(x, dict) for x in v):
        return v
    raise ValueError(f"{field_name} must be a list of objects")


@dataclass(frozen=True)
class VisualThresholds:
    """Allowable thresholds for pixel, LPIPS, and DISTS measurements."""

    pixel_max: float
    lpips_max: float
    dists_max: float

    pixel_uncertain_delta: float | None = None
    lpips_uncertain_delta: float | None = None
    dists_uncertain_delta: float | None = None
    shift_compensation_y_px: int | None = None

    def __post_init__(self) -> None:
        if self.pixel_max < 0 or self.lpips_max < 0 or self.dists_max < 0:
            raise ValueError("Thresholds must be >= 0")

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> VisualThresholds:
        if d is None:
            d = {}
        if not isinstance(d, dict):
            raise ValueError("thresholds must be an object")
        return cls(
            pixel_max=_opt_float(d, "pixel_max", 0.0),
            lpips_max=_opt_float(d, "lpips_max", 0.0),
            dists_max=_opt_float(d, "dists_max", 0.0),
            pixel_uncertain_delta=d.get("pixel_uncertain_delta") if "pixel_uncertain_delta" in d else None,
            lpips_uncertain_delta=d.get("lpips_uncertain_delta") if "lpips_uncertain_delta" in d else None,
            dists_uncertain_delta=d.get("dists_uncertain_delta") if "dists_uncertain_delta" in d else None,
            shift_compensation_y_px=(
                _opt_int(d, "shift_compensation_y_px", 0) if "shift_compensation_y_px" in d else None
            ),
        )


@dataclass(frozen=True)
class VisualMask:
    """Optional DOM locators that receive translucent overlay masking."""

    locators: tuple[str, ...] = ()
    color: str = DEFAULT_MASK_COLOR

    def __post_init__(self) -> None:
        # Very basic validation (#RRGGBB)
        if not (isinstance(self.color, str) and self.color.startswith("#") and len(self.color) == 7):
            raise ValueError(f"Invalid mask color: {self.color!r}")

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> VisualMask:
        if d is None:
            return cls()
        if not isinstance(d, dict):
            raise ValueError("mask must be an object")
        locators_raw = d.get("locators") if "locators" in d else d.get("selectors")
        return cls(
            locators=_as_tuple_str(locators_raw),
            color=_opt_str(d, "color", DEFAULT_MASK_COLOR),
        )


@dataclass(frozen=True)
class VisualCapture:
    """Defines how screenshots should be captured (page/viewport/element)."""

    capture_type: CaptureType = "page"
    locator: str = ""
    full_page: bool = True

    def __post_init__(self) -> None:
        if self.capture_type == "element" and not self.locator.strip():
            raise ValueError("capture.locator is required when capture_type='element'")

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> VisualCapture:
        if d is None:
            return cls()
        if not isinstance(d, dict):
            raise ValueError("capture must be an object")

        # Your schema uses "type"
        raw_type = _opt_str(d, "type", "page").strip().lower()
        if raw_type not in ("page", "viewport", "element"):
            raise ValueError(f"Invalid capture.type: {raw_type!r}")

        return cls(
            capture_type=cast(CaptureType, raw_type),
            locator=_opt_str(d, "locator", _opt_str(d, "selector", "")),
            full_page=_opt_bool(d, "full_page", True),
        )


@dataclass(frozen=True)
class VisualStep:
    """Represents a UI interaction that can run before capturing.

    Kept flexible (action is str) because your steps JSON may evolve.
    """

    action: str
    selector: str = ""
    value: str = ""
    timeout_ms: int = 5000
    url: str = ""

    def __post_init__(self) -> None:
        if self.timeout_ms < 0:
            raise ValueError("timeout_ms must be >= 0")

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VisualStep:
        if not isinstance(d, dict):
            raise ValueError("step must be an object")
        action = _require_str(d, "action").strip().lower()
        timeout_ms = d.get("timeout_ms", 5000)
        if not isinstance(timeout_ms, int):
            raise ValueError("step.timeout_ms must be an int")
        return cls(
            action=action,
            selector=_opt_str(d, "selector", ""),
            value=_opt_str(d, "value", ""),
            timeout_ms=timeout_ms,
            url=_opt_str(d, "url", ""),
        )


@dataclass(frozen=True)
class VisualScenario:
    """Describes a single visual regression scenario, its capture, and thresholds."""

    scenario_id: str
    name: str
    target_url: str
    suite_id: str
    compare_mode: CompareMode
    viewport: tuple[str, ...]
    capture: VisualCapture
    thresholds: VisualThresholds
    mask: VisualMask = field(default_factory=VisualMask)
    steps: tuple[VisualStep, ...] = ()
    perceptual_required: bool = False
    raw_definition: dict[str, Any] = field(default_factory=dict)
    source_file: str = ""

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")
        if not self.suite_id.strip():
            raise ValueError("suite_id must be non-empty")
        if not self.target_url.strip():
            raise ValueError("target_url must be non-empty")

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VisualScenario:
        if not isinstance(d, dict):
            raise ValueError("scenario must be an object")

        # Your schema: "id" + optionally accept "scenario_id" too
        scenario_id = _opt_str(d, "id", "").strip() or _require_str(d, "scenario_id")

        compare_mode = _require_str(d, "compare_mode").strip().lower()
        if compare_mode not in ("pixel", "hybrid"):
            raise ValueError(f"Invalid compare_mode: {compare_mode!r}")

        steps_raw = _as_tuple_dict(d.get("steps"), "steps")
        steps = tuple(VisualStep.from_dict(s) for s in steps_raw)

        return cls(
            scenario_id=scenario_id,
            name=_require_str(d, "name"),
            target_url=_require_str(d, "target_url"),
            suite_id=_require_str(d, "suite_id"),
            compare_mode=cast(CompareMode, compare_mode),
            viewport=_as_tuple_str(d.get("viewport")),
            capture=VisualCapture.from_dict(d.get("capture")),
            thresholds=VisualThresholds.from_dict(d.get("thresholds")),
            mask=VisualMask.from_dict(d.get("mask")),
            steps=steps,
            perceptual_required=_opt_bool(d, "perceptual_required", False),
            raw_definition=deepcopy(d),
        )


@dataclass
class VisualResult:
    """Outcome record produced by running a VisualScenario."""

    scenario_id: str
    status: ResultStatus
    message: str
    compare_mode: CompareMode

    baseline_path: str
    actual_path: str
    diff_path: str = ""
    comparison_baseline_path: str = ""
    comparison_actual_path: str = ""
    heatmap_path: str = ""

    suite_id: str = ""
    viewport: str = ""
    browser: str = ""
    nodeid: str = ""

    pixel_changed_ratio: float | None = None
    applied_shift_y: int | None = None
    shift_compensation_y_px_effective: int | None = None
    shift_compensation_y_px_env_default: int | None = None
    shift_compensation_y_px_scenario_override: int | None = None
    shift_compensation_y_px_source: str | None = None
    lpips: float | None = None
    dists: float | None = None

    thresholds: VisualThresholds | None = None
    tester: str = ""
    run_note: str = ""
    test_metadata: dict[str, Any] | None = None
    perceptual: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status,
            "message": self.message,
            "compare_mode": self.compare_mode,
            "suite_id": self.suite_id,
            "viewport": self.viewport,
            "browser": self.browser,
            "nodeid": self.nodeid,
            "baseline_path": self.baseline_path,
            "actual_path": self.actual_path,
            "diff_path": self.diff_path,
            "comparison_baseline_path": self.comparison_baseline_path,
            "comparison_actual_path": self.comparison_actual_path,
            "heatmap_path": self.heatmap_path,
            "pixel_changed_ratio": self.pixel_changed_ratio,
            "applied_shift_y": self.applied_shift_y,
            "shift_compensation_y_px_effective": self.shift_compensation_y_px_effective,
            "shift_compensation_y_px_env_default": self.shift_compensation_y_px_env_default,
            "shift_compensation_y_px_scenario_override": self.shift_compensation_y_px_scenario_override,
            "shift_compensation_y_px_source": self.shift_compensation_y_px_source,
            "lpips": self.lpips,
            "dists": self.dists,
            "thresholds": (
                {
                    "pixel_max": self.thresholds.pixel_max,
                    "lpips_max": self.thresholds.lpips_max,
                    "dists_max": self.thresholds.dists_max,
                    "pixel_uncertain_delta": self.thresholds.pixel_uncertain_delta,
                    "lpips_uncertain_delta": self.thresholds.lpips_uncertain_delta,
                    "dists_uncertain_delta": self.thresholds.dists_uncertain_delta,
                    "shift_compensation_y_px": self.thresholds.shift_compensation_y_px,
                }
                if self.thresholds
                else None
            ),
            "tester": self.tester,
            "run_note": self.run_note,
            "test_metadata": self.test_metadata,
            "perceptual": self.perceptual,
        }


def load_visual_scenarios_json(path: Path) -> tuple[VisualScenario, ...]:
    """Load visual scenarios from a JSON file.

    Supports top-level:
      - a single scenario object
      - a list of scenario objects
      - {"scenarios": [ ... ]}
    """
    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, dict) and "scenarios" in data:
        scenarios_raw = data["scenarios"]
    else:
        scenarios_raw = data

    if isinstance(scenarios_raw, dict):
        scenarios_raw = [scenarios_raw]

    if not isinstance(scenarios_raw, list) or not all(isinstance(x, dict) for x in scenarios_raw):
        raise ValueError("JSON must be a scenario object, a list of scenario objects, or {'scenarios': [...]}")

    return tuple(VisualScenario.from_dict(s) for s in scenarios_raw)
