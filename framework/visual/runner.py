from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

from framework.env import RuntimeEnv
from framework.visual.baseline_store import BaselineStore
from framework.visual.compare_pixel import compare_images
from framework.visual.models import VisualResult, VisualScenario
from framework.visual.perceptual_client import PerceptualClient, PerceptualServiceError


class VisualRunner:
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
        self._perceptual = PerceptualClient(env)

    @property
    def perceptual_client(self) -> PerceptualClient:
        return self._perceptual

    def run(self, page: Page, scenario: VisualScenario, viewport: str, approve: bool) -> VisualResult:
        self._navigate(page, scenario)
        actual_path = self._actual_dir / f"{scenario.scenario_id}.png"
        self._capture(page, scenario, actual_path)

        browser_family = page.context.browser.browser_type.name
        baseline_path = self._store.resolve_baseline(
            scenario.suite_id,
            scenario.scenario_id,
            viewport,
            browser_family,
        )

        if approve:
            saved = self._store.store_baseline(
                scenario.suite_id,
                scenario.scenario_id,
                viewport,
                browser_family,
                actual_path,
            )
            return VisualResult(
                scenario_id=scenario.scenario_id,
                status="approved",
                message="Baseline approved",
                compare_mode=scenario.compare_mode,
                baseline_path=str(saved),
                actual_path=str(actual_path),
                diff_path="",
                heatmap_path="",
                pixel_changed_ratio=0.0,
                lpips=None,
                dists=None,
                thresholds=scenario.thresholds,
            )

        if baseline_path is None:
            status = "failed" if self._env.visual_fail_on_missing_baseline else "new"
            return VisualResult(
                scenario_id=scenario.scenario_id,
                status=status,
                message="Baseline missing",
                compare_mode=scenario.compare_mode,
                baseline_path="",
                actual_path=str(actual_path),
                diff_path="",
                heatmap_path="",
                pixel_changed_ratio=1.0,
                lpips=None,
                dists=None,
                thresholds=scenario.thresholds,
            )

        diff_path = self._diff_dir / f"{scenario.scenario_id}.png"
        pixel_changed_ratio = compare_images(baseline_path, actual_path, diff_path)

        lpips_score: float | None = None
        dists_score: float | None = None
        heatmap_path = ""
        mode_effective = scenario.compare_mode

        requires_perceptual = scenario.compare_mode in {"perceptual", "hybrid"}
        must_have_perceptual = self._env.visual_perceptual_required or scenario.perceptual_required
        if requires_perceptual:
            available = self._perceptual.ensure_ready(required=must_have_perceptual)
            if available:
                try:
                    response = self._perceptual.compare(baseline_path, actual_path)
                    lpips_score = float(response.get("lpips", {}).get("value", 0.0))
                    dists_score = float(response.get("dists", {}).get("value", 0.0))
                    heatmap_b64 = str(response.get("lpips_heatmap_png_base64", ""))
                    if heatmap_b64:
                        heatmap_file = self._heatmap_dir / f"{scenario.scenario_id}.png"
                        heatmap_file.write_bytes(base64.b64decode(heatmap_b64))
                        heatmap_path = str(heatmap_file)
                except PerceptualServiceError as exc:
                    if must_have_perceptual or self._env.visual_perceptual_fallback_mode == "abort":
                        return VisualResult(
                            scenario_id=scenario.scenario_id,
                            status="failed",
                            message=f"Perceptual compare failed: {exc}",
                            compare_mode=scenario.compare_mode,
                            baseline_path=str(baseline_path),
                            actual_path=str(actual_path),
                            diff_path=str(diff_path),
                            heatmap_path=heatmap_path,
                            pixel_changed_ratio=pixel_changed_ratio,
                            lpips=None,
                            dists=None,
                            thresholds=scenario.thresholds,
                        )
                    mode_effective = "pixel"
            else:
                mode_effective = "pixel"

        status, message = _evaluate(
            mode_effective,
            pixel_changed_ratio,
            lpips_score,
            dists_score,
            scenario.thresholds.pixel_max,
            scenario.thresholds.lpips_max,
            scenario.thresholds.dists_max,
        )

        return VisualResult(
            scenario_id=scenario.scenario_id,
            status=status,
            message=message,
            compare_mode=mode_effective,
            baseline_path=str(baseline_path),
            actual_path=str(actual_path),
            diff_path=str(diff_path),
            heatmap_path=heatmap_path,
            pixel_changed_ratio=pixel_changed_ratio,
            lpips=lpips_score,
            dists=dists_score,
            thresholds=scenario.thresholds,
        )

    def _navigate(self, page: Page, scenario: VisualScenario) -> None:
        if scenario.target_url:
            if scenario.target_url.startswith("http://") or scenario.target_url.startswith("https://"):
                page.goto(scenario.target_url)
            else:
                base = self._env.base_url.rstrip("/")
                page.goto(f"{base}/{scenario.target_url.lstrip('/')}")
        for step in scenario.steps:
            self._run_step(page, step.action, step.selector, step.value, step.timeout_ms, step.url)

    def _run_step(self, page: Page, action: str, selector: str, value: str, timeout_ms: int, url: str) -> None:
        if action == "click" and selector:
            page.locator(selector).first.click(timeout=timeout_ms)
            return
        if action == "fill" and selector:
            page.locator(selector).first.fill(value, timeout=timeout_ms)
            return
        if action == "wait_for_selector" and selector:
            page.wait_for_selector(selector, timeout=timeout_ms)
            return
        if action == "wait" or action == "wait_for_timeout":
            page.wait_for_timeout(timeout_ms)
            return
        if action == "goto":
            page.goto(url or value, timeout=timeout_ms)

    def _capture(self, page: Page, scenario: VisualScenario, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cleanup_js = _inject_masks(page, list(scenario.mask.selectors), scenario.mask.color)
        try:
            if scenario.capture.capture_type == "element" and scenario.capture.selector:
                page.locator(scenario.capture.selector).first.screenshot(path=str(output_path))
                return
            page.screenshot(path=str(output_path), full_page=scenario.capture.full_page)
        finally:
            _remove_masks(page, cleanup_js)


def _inject_masks(page: Page, selectors: list[str], color: str) -> list[str]:
    if not selectors:
        return []
    script = """
    (params) => {
      const ids = [];
      const color = params.color || '#00FF00';
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
        data: Any = page.evaluate(script, {"selectors": selectors, "color": color})
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        return []
    return []


def _remove_masks(page: Page, ids: list[str]) -> None:
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
) -> tuple[str, str]:
    if mode == "pixel":
        if pixel_changed_ratio <= pixel_max:
            return "passed", "Pixel threshold passed"
        return "failed", "Pixel threshold exceeded"

    lpips_ok = lpips is not None and lpips <= lpips_max
    dists_ok = dists is not None and dists <= dists_max
    perceptual_ok = lpips_ok and dists_ok

    if mode == "perceptual":
        if perceptual_ok:
            return "passed", "Perceptual thresholds passed"
        return "failed", "Perceptual thresholds exceeded"

    pixel_ok = pixel_changed_ratio <= pixel_max
    if perceptual_ok and pixel_ok:
        return "passed", "Pixel and perceptual thresholds passed"
    if perceptual_ok and not pixel_ok:
        return "warn", "Pixel exceeded, perceptual passed"
    return "failed", "Perceptual thresholds exceeded"
