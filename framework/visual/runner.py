from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

from playwright.sync_api import Locator, Page

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


def _resolve_shift_compensation_y_px(env_shift_px: int, scenario_shift_px: int | None) -> int:
    if scenario_shift_px is not None:
        return max(0, int(scenario_shift_px))
    return max(0, int(env_shift_px))


class VisualRunner:
    """Capture actual screenshots, compare to baselines, and return VisualResult."""

    def __init__(self, env: RuntimeEnv, repo_root: Path, output_dir: Path) -> None:
        self._env = env
        self._store = BaselineStore(env, repo_root)
        self._output_dir = output_dir
        self._actual_dir = output_dir / "actual"
        self._diff_dir = output_dir / "diff"
        self._normalized_dir = output_dir / "normalized"
        self._heatmap_dir = output_dir / "heatmap"
        self._actual_dir.mkdir(parents=True, exist_ok=True)
        self._diff_dir.mkdir(parents=True, exist_ok=True)
        self._normalized_dir.mkdir(parents=True, exist_ok=True)
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

        shift_compensation_y_px_env_default = max(0, int(self._env.visual_shift_compensation_y_px))
        scenario_shift_raw = getattr(scenario.thresholds, "shift_compensation_y_px", None)
        shift_compensation_y_px_scenario_override = (
            max(0, int(scenario_shift_raw)) if scenario_shift_raw is not None else None
        )
        shift_compensation_y_px = _resolve_shift_compensation_y_px(
            shift_compensation_y_px_env_default,
            shift_compensation_y_px_scenario_override,
        )
        shift_compensation_y_px_source = (
            "scenario_override" if shift_compensation_y_px_scenario_override is not None else "env_default"
        )

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
                applied_shift_y=0,
                shift_compensation_y_px_effective=shift_compensation_y_px,
                shift_compensation_y_px_env_default=shift_compensation_y_px_env_default,
                shift_compensation_y_px_scenario_override=shift_compensation_y_px_scenario_override,
                shift_compensation_y_px_source=shift_compensation_y_px_source,
                lpips=None,
                dists=None,
                thresholds=scenario.thresholds,
            )

        diff_path = self._diff_dir / f"{file_stem}.png"
        comparison_baseline_path = self._normalized_dir / f"{file_stem}__baseline.png"
        comparison_actual_path = self._normalized_dir / f"{file_stem}__actual.png"
        pixel_out = compare_images(
            baseline_path,
            actual_path,
            diff_path,
            shift_compensation_y_px=shift_compensation_y_px,
            return_details=True,
            normalized_baseline_path=comparison_baseline_path,
            normalized_actual_path=comparison_actual_path,
        )
        pixel_changed_ratio = float(cast(dict[str, Any], pixel_out).get("changed_ratio", 1.0))
        applied_shift_y = int(cast(dict[str, Any], pixel_out).get("applied_shift_y", 0) or 0)

        lpips_score: float | None = None
        dists_score: float | None = None
        heatmap_path_str = ""
        mode_effective = str(getattr(scenario, "compare_mode", "pixel") or "pixel").strip().lower()
        if mode_effective not in {"pixel", "hybrid"}:
            mode_effective = "pixel"

        if mode_effective == "hybrid" and self._env.pms_enabled and str(self._env.pms_base_url or "").strip():
            status, message = "analysis", "Perceptual analysis in progress"
        else:
            status, message = _evaluate(
                "pixel" if mode_effective == "hybrid" else mode_effective,
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
            comparison_baseline_path=str(comparison_baseline_path),
            comparison_actual_path=str(comparison_actual_path),
            heatmap_path=heatmap_path_str,
            pixel_changed_ratio=pixel_changed_ratio,
            applied_shift_y=applied_shift_y,
            shift_compensation_y_px_effective=shift_compensation_y_px,
            shift_compensation_y_px_env_default=shift_compensation_y_px_env_default,
            shift_compensation_y_px_scenario_override=shift_compensation_y_px_scenario_override,
            shift_compensation_y_px_source=shift_compensation_y_px_source,
            lpips=lpips_score,
            dists=dists_score,
            thresholds=scenario.thresholds,
        )

    def _navigate(self, page: Page, scenario: VisualScenario) -> None:
        """Navigate to the scenario URL and execute all preparatory steps."""
        if scenario.target_url:
            if scenario.target_url.startswith(("http://", "https://")):
                response = page.goto(scenario.target_url)
                self._assert_navigation_response(response, scenario.target_url)
            else:
                base = self._env.base_url.rstrip("/")
                target = f"{base}/{scenario.target_url.lstrip('/')}"
                response = page.goto(target)
                self._assert_navigation_response(response, target)
        for step in scenario.steps:
            self._run_step(page, step.action, step.selector, step.value, step.timeout_ms, step.url)

    @staticmethod
    def _assert_navigation_response(response: Any, target: str) -> None:
        """Fail fast when navigation ends with HTTP error or missing response."""
        if response is None:
            raise ValueError(f"Navigation failed without HTTP response: {target}")
        status_raw = getattr(response, "status", None)
        try:
            status = int(cast(Any, status_raw))
        except (TypeError, ValueError) as err:
            raise ValueError(f"Navigation failed with invalid HTTP status for: {target}") from err
        if status >= 400:
            response_url = str(getattr(response, "url", "") or target)
            raise ValueError(f"Navigation failed with HTTP {status}: {response_url}")

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
            response = page.goto(target, timeout=timeout_ms)
            self._assert_navigation_response(response, target)
            return

        raise ValueError(f"Unknown step action: {action!r}")

    def _capture(self, page: Page, scenario: VisualScenario, output_path: Path) -> None:
        """Capture the screenshot based on capture settings while masking selectors."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        freeze_style_id = _inject_freeze_styles(page) if bool(self._env.visual_freeze_animations) else ""
        if scenario.capture.full_page:
            _stabilize_full_page_capture(page)
        mask_locators = _build_mask_locators(page, list(scenario.mask.selectors))
        mask_color = _hex_to_rgba(scenario.mask.color, alpha=1)
        try:
            if scenario.capture.capture_type == "element" and scenario.capture.selector:
                target_locator = _first_visible_locator(page.locator(scenario.capture.selector))
                scroll_lock_style_id = _stabilize_element_capture(page, target_locator)
                try:
                    if mask_locators:
                        target_locator.screenshot(path=str(output_path), mask=mask_locators, mask_color=mask_color)
                    else:
                        target_locator.screenshot(path=str(output_path))
                finally:
                    _remove_freeze_styles(page, scroll_lock_style_id)
                return
            if mask_locators:
                page.screenshot(
                    path=str(output_path),
                    full_page=scenario.capture.full_page,
                    mask=mask_locators,
                    mask_color=mask_color,
                )
            else:
                page.screenshot(path=str(output_path), full_page=scenario.capture.full_page)
        finally:
            _remove_freeze_styles(page, freeze_style_id)


def _first_visible_locator(locator: Locator) -> Locator:
    """Return the first visible match, falling back to the first locator."""
    try:
        count = locator.count()
    except Exception:
        return locator.first

    for index in range(count):
        candidate = locator.nth(index)
        try:
            if candidate.is_visible():
                return candidate
        except Exception:
            continue
    return locator.first


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


def _build_mask_locators(page: Page, selectors: list[str]) -> list[Locator]:
    """Build mask locators from scenario mask selectors."""
    locators: list[Locator] = []
    for selector in selectors:
        token = str(selector or "").strip()
        if not token:
            continue
        try:
            locators.append(page.locator(token))
        except Exception:
            continue
    return locators


def _stabilize_full_page_capture(page: Page) -> None:
    """Best-effort pre-capture stabilization for lazy-loaded full-page content."""
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass

    try:
        page.evaluate("""
            () => new Promise((resolve) => {
              const doc = document.scrollingElement || document.documentElement;
              const maxY = Math.max(0, (doc?.scrollHeight || 0) - window.innerHeight);
              if (maxY <= 0) {
                window.scrollTo(0, 0);
                setTimeout(resolve, 100);
                return;
              }

              const step = Math.max(Math.floor(window.innerHeight * 0.75), 200);
              const delay = 120;
              let y = 0;

              const tick = () => {
                y = Math.min(y + step, maxY);
                window.scrollTo(0, y);
                if (y >= maxY) {
                  setTimeout(() => {
                    window.scrollTo(0, 0);
                    setTimeout(resolve, delay);
                  }, delay);
                  return;
                }
                setTimeout(tick, delay);
              };

              tick();
            })
            """)
    except Exception:
        pass

    try:
        page.evaluate("""
            () => Promise.all([
              (document.fonts && document.fonts.ready)
                ? document.fonts.ready.catch(() => undefined)
                : Promise.resolve(),
              new Promise((resolve) => {
                const images = Array.from(document.images || []);
                const pending = images.filter((img) => !img.complete);
                if (!pending.length) {
                  resolve(undefined);
                  return;
                }
                let done = 0;
                const finish = () => {
                  done += 1;
                  if (done >= pending.length) {
                    resolve(undefined);
                  }
                };
                pending.forEach((img) => {
                  img.addEventListener("load", finish, { once: true });
                  img.addEventListener("error", finish, { once: true });
                });
                setTimeout(() => resolve(undefined), 1500);
              }),
            ])
            """)
    except Exception:
        pass

    try:
        page.wait_for_timeout(150)
    except Exception:
        pass


def _stabilize_element_capture(page: Page, locator: Locator) -> str:
    """Stabilize element capture and lock page scrolling during screenshot."""
    try:
        page.wait_for_load_state("networkidle", timeout=3000)
    except Exception:
        pass

    try:
        locator.scroll_into_view_if_needed(timeout=3000)
    except Exception:
        pass

    scroll_lock_style_id = _inject_scroll_lock_styles(page)

    try:
        page.wait_for_timeout(120)
    except Exception:
        pass

    return scroll_lock_style_id


def _inject_freeze_styles(page: Page) -> str:
    style_id = "visual-freeze-style"
    script = """
    (styleId) => {
      try {
        const existing = document.getElementById(styleId);
        if (existing) {
          return styleId;
        }
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
          *, *::before, *::after {
            animation: none !important;
            transition: none !important;
            caret-color: transparent !important;
          }
          html, body {
            scroll-behavior: auto !important;
          }
        `;
        document.head.appendChild(style);
        return styleId;
      } catch (_) {
        return "";
      }
    }
    """
    try:
        value = page.evaluate(script, style_id)
        return str(value or "")
    except Exception:
        return ""


def _inject_scroll_lock_styles(page: Page) -> str:
    style_id = "visual-scroll-lock-style"
    script = """
    (styleId) => {
      try {
        const existing = document.getElementById(styleId);
        if (existing) {
          return styleId;
        }
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
          html, body {
            overflow: hidden !important;
            overscroll-behavior: none !important;
            scroll-behavior: auto !important;
          }
        `;
        document.head.appendChild(style);
        return styleId;
      } catch (_) {
        return "";
      }
    }
    """
    try:
        value = page.evaluate(script, style_id)
        return str(value or "")
    except Exception:
        return ""


def _remove_freeze_styles(page: Page, style_id: str) -> None:
    token = str(style_id or "").strip()
    if not token:
        return
    script = """
    (styleId) => {
      const el = document.getElementById(styleId);
      if (el) {
        el.remove();
      }
    }
    """
    try:
        page.evaluate(script, token)
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

    # hybrid
    pixel_ok = pixel_changed_ratio <= pixel_max
    if perceptual_ok and pixel_ok:
        return "passed", "Pixel and perceptual thresholds passed"
    if perceptual_ok and not pixel_ok:
        if uncertain_enabled and _in_uncertain_zone(pixel_changed_ratio, pixel_max, pixel_uncertain_delta):
            return "uncertain", "Pixel within uncertainty zone"
        return "uncertain", "Pixel exceeded, perceptual passed"
    return "failed", "Perceptual thresholds exceeded"
