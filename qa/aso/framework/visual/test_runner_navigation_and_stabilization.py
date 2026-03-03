from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from framework.env import load_env
from framework.visual.models import VisualScenario
from framework.visual.runner import VisualRunner

pytestmark = [pytest.mark.aso]


def _env():
    return replace(load_env(), base_url="https://example.test")


def _scenario(*, full_page: bool = True, target_url: str = "/") -> VisualScenario:
    return VisualScenario.from_dict(
        {
            "id": "scenario-1",
            "name": "Scenario 1",
            "target_url": target_url,
            "suite_id": "suite-1",
            "compare_mode": "pixel",
            "capture": {"type": "page", "full_page": full_page},
            "thresholds": {"pixel_max": 0.01, "lpips_max": 0.1, "dists_max": 0.1},
        }
    )


def _runner(tmp_path: Path) -> VisualRunner:
    return VisualRunner(_env(), repo_root=tmp_path, output_dir=tmp_path / "visual")


class _NavPage:
    def __init__(self, statuses: list[int | None]):
        self._statuses = list(statuses)
        self.goto_calls: list[str] = []

    def goto(self, url: str, **kwargs):
        _ = kwargs
        self.goto_calls.append(url)
        if not self._statuses:
            return SimpleNamespace(status=200, url=url)
        status = self._statuses.pop(0)
        if status is None:
            return None
        return SimpleNamespace(status=status, url=url)


class _CapturePage:
    def __init__(self):
        self.wait_for_load_state_calls: list[tuple[str, int]] = []
        self.wait_for_timeout_calls: list[int] = []
        self.evaluate_calls = 0
        self.screenshot_calls: list[bool] = []

    def wait_for_load_state(self, state: str, timeout: int = 0):
        self.wait_for_load_state_calls.append((state, timeout))

    def evaluate(self, script, arg=None):
        _ = arg
        self.evaluate_calls += 1
        script_text = str(script)
        if "visual-mask-" in script_text:
            return []
        return None

    def wait_for_timeout(self, timeout_ms: int):
        self.wait_for_timeout_calls.append(timeout_ms)

    def screenshot(self, *, path: str, full_page: bool):
        _ = path
        self.screenshot_calls.append(full_page)


def test_navigate_fails_on_http_404(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    page = _NavPage([404])

    with pytest.raises(ValueError, match=r"HTTP 404"):
        runner._navigate(page, _scenario(target_url="/missing"))


def test_step_goto_fails_on_http_404(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    page = _NavPage([404])

    with pytest.raises(ValueError, match=r"HTTP 404"):
        runner._run_step(page, "goto", "", "https://example.test/missing", 5000, "")


def test_capture_stabilizes_only_for_full_page(tmp_path: Path) -> None:
    runner = _runner(tmp_path)

    page_full = _CapturePage()
    runner._capture(page_full, _scenario(full_page=True), tmp_path / "full.png")
    assert page_full.wait_for_load_state_calls
    assert page_full.screenshot_calls == [True]

    page_viewport = _CapturePage()
    runner._capture(page_viewport, _scenario(full_page=False), tmp_path / "viewport.png")
    assert page_viewport.wait_for_load_state_calls == []
    assert page_viewport.screenshot_calls == [False]
