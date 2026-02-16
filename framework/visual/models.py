from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VisualThresholds:
    pixel_max: float
    lpips_max: float
    dists_max: float


@dataclass(frozen=True)
class VisualMask:
    selectors: tuple[str, ...] = ()
    color: str = "#00FF00"


@dataclass(frozen=True)
class VisualCapture:
    capture_type: str = "page"  # page|viewport|element
    selector: str = ""
    full_page: bool = True


@dataclass(frozen=True)
class VisualStep:
    action: str
    selector: str = ""
    value: str = ""
    timeout_ms: int = 5000
    url: str = ""


@dataclass(frozen=True)
class VisualScenario:
    scenario_id: str
    name: str
    target_url: str
    suite_id: str
    compare_mode: str
    capture: VisualCapture
    thresholds: VisualThresholds
    mask: VisualMask = field(default_factory=VisualMask)
    steps: tuple[VisualStep, ...] = ()
    perceptual_required: bool = False


@dataclass
class VisualResult:
    scenario_id: str
    status: str
    message: str
    compare_mode: str
    baseline_path: str
    actual_path: str
    diff_path: str
    heatmap_path: str
    pixel_changed_ratio: float
    lpips: float | None
    dists: float | None
    thresholds: VisualThresholds
