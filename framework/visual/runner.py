from __future__ import annotations
import re
from pathlib import Path
from typing import Any, cast
from playwright.sync_api import Page
from framework.env import RuntimeEnv
from framework.visual.baseline_store import BaselineStore
from framework.visual.compare_pixel import compare_images
from framework.visual.models import VisualResult, VisualScenario


"""Driver for executing visual regression scenarios and emitting comparison results."""

_SAFE_FILE = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_filename(stem: str) -> str:
    """Make a safe filename stem from scenario id."""
    s = stem.strip()
    s = s.replace("\\", "_").replace("/", "_")
    s = _SAFE_FILE.sub("_", s)
    return s or "scenario"


def _safe_float(value: object, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(cast(Any, value))
    except (TypeError, ValueError):
        return default


class VisualRunner:
    """Capture actual screenshots, compare to baselines, and return VisualResult."""

    def __init__(self, env: RuntimeEnv, repo_root: Path, output_dir: Path) -> None:
        self._env = env
        self._store = BaselineStore(env, repo_root)
        self._output_dir = output_dir
        self._actual_dir = output_dir / "actual"
        self._diff_dir = output_dir / "diff"
        self._heatmap_dir = output_dir / "heatmap"
        self._actual_dir.mkdir(parents=True, exist_ok=True)
        self._diff_dir.mkdir(parents=True, exist_ok=True)
        self._heatmap_dir.mkdir(parents=True, exist_ok=True)

    def run(self, page: Page, scenario: VisualScenario, viewport: str) -> VisualResult:
        """Execute the scenario, compare captures, and either approve or evaluate."""

        self._navigate(page, scenario)

        viewport_token = (viewport or "").strip() or "default"
        file_stem = _safe_filename(f"{scenario.scenario_id}__{viewport_token}")
        actual_path = self._actual_dir / f"{file_stem}.png"
        self._capture(page, scenario, actual_path)

        # Browser family (be defensive)
        browser_family = "unknown"
        try:
            b = page.context.browser
            if b is not None:
                browser_family = b.browser_type.name
        except Exception:
            browser_family = (self._env.browser or "unknown").strip().lower()

        baseline_path = self._store.resolve_baseline(
            scenario.suite_id,
            scenario.scenario_id,
            viewport_token,
            browser_family,
        )
        if baseline_path is None:
            status = "failed" if self._env.visual_fail_on_missing_baseline else "new"
            return VisualResult(
                scenario_id=scenario.scenario_id,
                status=status,
                message="Baseline missing",
                compare_mode=scenario.compare_mode,
                suite_id=scenario.suite_id,
                viewport=viewport_token,
                browser=browser_family,
                baseline_path="",
                actual_path=str(actual_path),
                diff_path="",
                heatmap_path="",
                pixel_changed_ratio=1.0,
                lpips=None,
                dists=None,
                thresholds=scenario.thresholds,
            )

        diff_path = self._diff_dir / f"{file_stem}.png"
        pixel_out = compare_images(baseline_path, actual_path, diff_path)
        pixel_changed_ratio = float(pixel_out[0]) if isinstance(pixel_out, tuple) else float(pixel_out)

        lpips_score: float | None = None
        dists_score: float | None = None
        heatmap_path_str = ""
        mode_effective = str(getattr(scenario, "compare_mode", "pixel") or "pixel").strip().lower()
        if mode_effective not in {"pixel", "hybrid"}:
            mode_effective = "pixel"

        status, message = _evaluate(
            mode_effective,
            pixel_changed_ratio,
            lpips_score,
            dists_score,
            scenario.thresholds.pixel_max,
            scenario.thresholds.lpips_max,
            scenario.thresholds.dists_max,
            self._env.visual_uncertain_enabled,
            scenario.thresholds.pixel_uncertain_delta or self._env.visual_uncertain_pixel_delta,
            scenario.thresholds.lpips_uncertain_delta or self._env.visual_uncertain_lpips_delta,
            scenario.thresholds.dists_uncertain_delta or self._env.visual_uncertain_dists_delta,
        )

        return VisualResult(
            scenario_id=scenario.scenario_id,
            status=cast(Any, status),
            message=message,
            compare_mode=cast(Any, mode_effective),
            suite_id=scenario.suite_id,
            viewport=viewport_token,
            browser=browser_family,
            baseline_path=str(baseline_path),
            actual_path=str(actual_path),
            diff_path=str(diff_path),
            heatmap_path=heatmap_path_str,
            pixel_changed_ratio=pixel_changed_ratio,
            lpips=lpips_score,
            dists=dists_score,
            thresholds=scenario.thresholds,
        )

    def _navigate(self, page: Page, scenario: VisualScenario) -> None:
        """Navigate to the scenario URL and execute all preparatory steps."""
        if scenario.target_url:
            if scenario.target_url.startswith(("http://", "https://")):
                page.goto(scenario.target_url)
            else:
                base = self._env.base_url.rstrip("/")
                page.goto(f"{base}/{scenario.target_url.lstrip('/')}")
        for step in scenario.steps:
            self._run_step(page, step.action, step.selector, step.value, step.timeout_ms, step.url)

    def _run_step(self, page: Page, action: str, selector: str, value: str, timeout_ms: int, url: str) -> None:
        """Perform a single action specified in the scenario, such as click or fill."""
        action = (action or "").strip().lower()

        if action == "click":
            if not selector:
                raise ValueError("step.click requires selector")
            page.locator(selector).first.click(timeout=timeout_ms)
            return

        if action == "fill":
            if not selector:
                raise ValueError("step.fill requires selector")
            page.locator(selector).first.fill(value, timeout=timeout_ms)
            return

        if action in {"wait_for_selector", "wait_for"}:
            if not selector:
                raise ValueError("step.wait_for_selector requires selector")
            page.wait_for_selector(selector, timeout=timeout_ms)
            return

        if action in {"wait", "wait_for_timeout"}:
            page.wait_for_timeout(timeout_ms)
            return

        if action == "goto":
            target = (url or value or "").strip()
            if not target:
                raise ValueError("step.goto requires url or value")
            page.goto(target, timeout=timeout_ms)
            return

        raise ValueError(f"Unknown step action: {action!r}")

    def _capture(self, page: Page, scenario: VisualScenario, output_path: Path) -> None:
        """Capture the screenshot based on capture settings while masking selectors."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cleanup_ids = _inject_masks(page, list(scenario.mask.selectors), scenario.mask.color)
        try:
            if scenario.capture.capture_type == "element" and scenario.capture.selector:
                page.locator(scenario.capture.selector).first.screenshot(path=str(output_path))
                return
            page.screenshot(path=str(output_path), full_page=scenario.capture.full_page)
        finally:
            _remove_masks(page, cleanup_ids)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert '#RRGGBB' to 'rgba(r,g,b,a)'. Fallback to the original string if invalid."""
    s = (hex_color or "").strip()
    if len(s) == 7 and s.startswith("#"):
        try:
            r = int(s[1:3], 16)
            g = int(s[3:5], 16)
            b = int(s[5:7], 16)
            a = max(0.0, min(1.0, float(alpha)))
            return f"rgba({r},{g},{b},{a})"
        except ValueError:
            return s
    return s


def _inject_masks(page: Page, selectors: list[str], color: str) -> list[str]:
    """Overlay the given selectors with translucent masks and return their DOM IDs."""
    if not selectors:
        return []

    rgba = _hex_to_rgba(color, alpha=1)

    script = """
    (params) => {
      const ids = [];
      const color = params.color || 'rgba(0,255,0,1)';
      for (const selector of params.selectors) {
        document.querySelectorAll(selector).forEach((el) => {
          const rect = el.getBoundingClientRect();
          const mask = document.createElement('div');
          const id = `visual-mask-${Math.random().toString(36).slice(2)}`;
          mask.id = id;
          mask.style.position = 'fixed';
          mask.style.left = `${rect.left}px`;
          mask.style.top = `${rect.top}px`;
          mask.style.width = `${rect.width}px`;
          mask.style.height = `${rect.height}px`;
          mask.style.background = color;
          mask.style.zIndex = '2147483647';
          mask.style.pointerEvents = 'none';
          document.body.appendChild(mask);
          ids.push(id);
        });
      }
      return ids;
    }
    """
    try:
        data: Any = page.evaluate(script, {"selectors": selectors, "color": rgba})
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        return []
    return []


def _remove_masks(page: Page, ids: list[str]) -> None:
    """Clean up DOM masks that were injected for the capture."""
    if not ids:
        return
    script = """
    (ids) => {
      for (const id of ids) {
        const el = document.getElementById(id);
        if (el) el.remove();
      }
    }
    """
    try:
        page.evaluate(script, ids)
    except Exception:
        return


def _evaluate(
    mode: str,
    pixel_changed_ratio: float,
    lpips: float | None,
    dists: float | None,
    pixel_max: float,
    lpips_max: float,
    dists_max: float,
    uncertain_enabled: bool,
    pixel_uncertain_delta: float,
    lpips_uncertain_delta: float,
    dists_uncertain_delta: float,
) -> tuple[str, str]:
    """Assess thresholds and return the status/message tuple."""
    mode = (mode or "").strip().lower()

    def _in_uncertain_zone(value: float | None, threshold: float, delta: float) -> bool:
        """Check if value is in the uncertainty zone (threshold < value <= threshold + delta)."""
        if value is None or delta <= 0:
            return False
        return threshold < value <= threshold + delta

    if mode == "pixel":
        if pixel_changed_ratio <= pixel_max:
            return "passed", "Pixel threshold passed"
        if uncertain_enabled and _in_uncertain_zone(pixel_changed_ratio, pixel_max, pixel_uncertain_delta):
            return "uncertain", "Pixel within uncertainty zone"
        return "failed", "Pixel threshold exceeded"

    lpips_ok = lpips is not None and lpips <= lpips_max
    dists_ok = dists is not None and dists <= dists_max
    perceptual_ok = lpips_ok and dists_ok

    if mode == "perceptual":
        if perceptual_ok:
            return "passed", "Perceptual thresholds passed"
        if uncertain_enabled:
            in_uncertain = _in_uncertain_zone(lpips, lpips_max, lpips_uncertain_delta) or _in_uncertain_zone(
                dists, dists_max, dists_uncertain_delta
            )
            if in_uncertain:
                return "uncertain", "Perceptual within uncertainty zone"
        return "failed", "Perceptual thresholds exceeded"

    # hybrid
    pixel_ok = pixel_changed_ratio <= pixel_max
    if perceptual_ok and pixel_ok:
        return "passed", "Pixel and perceptual thresholds passed"
    if perceptual_ok and not pixel_ok:
        if uncertain_enabled and _in_uncertain_zone(pixel_changed_ratio, pixel_max, pixel_uncertain_delta):
            return "uncertain", "Pixel within uncertainty zone"
        return "uncertain", "Pixel exceeded, perceptual passed"
    return "failed", "Perceptual thresholds exceeded"
