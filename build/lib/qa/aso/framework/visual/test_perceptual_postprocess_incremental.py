from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from framework.env import load_env
from framework.visual.models import VisualResult, VisualThresholds
from framework.visual.perceptual_client import postprocess

pytestmark = [pytest.mark.aso]


def _runtime_env():
    return replace(
        load_env(),
        pms_enabled=True,
        pms_base_url="http://pms.local",
        pms_metric="lpips",
        pms_model="default",
        pms_normalize=False,
        pms_submit_rps=0.0,
        pms_poll_rps=0.0,
        pms_max_inflight=1,
        pms_server_active_limit=5,
        pms_timeout_sec=1,
        pms_retry_max=0,
        pms_health_timeout_seconds=1,
        pms_poll_interval_ms=100,
    )


def _make_result(tmp_path: Path) -> VisualResult:
    report_dir = tmp_path / "visual"
    report_dir.mkdir(parents=True, exist_ok=True)
    baseline = report_dir / "baseline.png"
    actual = report_dir / "actual.png"
    baseline.write_bytes(b"baseline")
    actual.write_bytes(b"actual")
    return VisualResult(
        scenario_id="hero",
        status="analysis",
        message="Perceptual analysis in progress",
        compare_mode="hybrid",
        baseline_path=str(baseline),
        actual_path=str(actual),
        pixel_changed_ratio=0.004,
        thresholds=VisualThresholds(pixel_max=0.005, lpips_max=0.08, dists_max=0.08),
        suite_id="suite",
        viewport="fhd",
        browser="chromium",
    )


def test_postprocess_calls_incremental_callback_on_done(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _DoneClient:
        def __init__(self, **_: object) -> None:
            self.enabled = True

        def health(self) -> bool:
            return True

        def list_jobs(self) -> list[dict[str, object]]:
            return []

        def submit_job(self, **_: object) -> None:
            return None

        def get_job(self, _job_id: str) -> dict[str, object]:
            return {"status": "done", "lpips": 0.05, "dists": 0.06}

        def download_heatmap(self, _job_id: str, _path: Path) -> bool:
            return False

        def get_job_error(self, _job_id: str) -> dict[str, object]:
            return {}

    monkeypatch.setattr(postprocess, "PMSClient", _DoneClient)
    result = _make_result(tmp_path)
    calls = {"count": 0}

    postprocess.run_perceptual_postprocess(
        env=_runtime_env(),
        run_id="run-1",
        report_dir=tmp_path / "visual",
        results=[result],
        on_results_updated=lambda: calls.__setitem__("count", calls["count"] + 1),
    )

    assert calls["count"] == 1
    assert result.perceptual and result.perceptual.get("status") == "done"


def test_postprocess_calls_incremental_callback_on_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _ErrorClient:
        def __init__(self, **_: object) -> None:
            self.enabled = True

        def health(self) -> bool:
            return True

        def list_jobs(self) -> list[dict[str, object]]:
            return []

        def submit_job(self, **_: object) -> None:
            return None

        def get_job(self, _job_id: str) -> dict[str, object]:
            return {"status": "error", "error_message": "boom"}

        def download_heatmap(self, _job_id: str, _path: Path) -> bool:
            return False

        def get_job_error(self, _job_id: str) -> dict[str, object]:
            return {}

    monkeypatch.setattr(postprocess, "PMSClient", _ErrorClient)
    result = _make_result(tmp_path)
    calls = {"count": 0}

    postprocess.run_perceptual_postprocess(
        env=_runtime_env(),
        run_id="run-2",
        report_dir=tmp_path / "visual",
        results=[result],
        on_results_updated=lambda: calls.__setitem__("count", calls["count"] + 1),
    )

    assert calls["count"] == 1
    assert result.perceptual and result.perceptual.get("status") == "error"


def test_postprocess_calls_incremental_callback_on_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _SlowClient:
        def __init__(self, **_: object) -> None:
            self.enabled = True

        def health(self) -> bool:
            return True

        def list_jobs(self) -> list[dict[str, object]]:
            return []

        def submit_job(self, **_: object) -> None:
            return None

        def get_job(self, _job_id: str) -> dict[str, object]:
            return {"status": "running"}

        def download_heatmap(self, _job_id: str, _path: Path) -> bool:
            return False

        def get_job_error(self, _job_id: str) -> dict[str, object]:
            return {}

    times = iter([0.0, 0.0, 2.0, 3.0])
    monkeypatch.setattr(postprocess, "PMSClient", _SlowClient)
    monkeypatch.setattr(postprocess.time, "monotonic", lambda: next(times))
    result = _make_result(tmp_path)
    calls = {"count": 0}

    postprocess.run_perceptual_postprocess(
        env=_runtime_env(),
        run_id="run-3",
        report_dir=tmp_path / "visual",
        results=[result],
        on_results_updated=lambda: calls.__setitem__("count", calls["count"] + 1),
    )

    assert calls["count"] == 1
    assert result.perceptual and result.perceptual.get("status") == "timeout"


def test_postprocess_falls_back_to_pixel_when_pms_job_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _ErrorClient:
        def __init__(self, **_: object) -> None:
            self.enabled = True

        def health(self) -> bool:
            return True

        def list_jobs(self) -> list[dict[str, object]]:
            return []

        def submit_job(self, **_: object) -> None:
            return None

        def get_job(self, _job_id: str) -> dict[str, object]:
            return {"status": "error", "error_message": "backend boom"}

        def download_heatmap(self, _job_id: str, _path: Path) -> bool:
            return False

        def get_job_error(self, _job_id: str) -> dict[str, object]:
            return {}

    monkeypatch.setattr(postprocess, "PMSClient", _ErrorClient)
    result = _make_result(tmp_path)

    postprocess.run_perceptual_postprocess(
        env=_runtime_env(),
        run_id="run-4",
        report_dir=tmp_path / "visual",
        results=[result],
        on_results_updated=None,
    )

    assert result.perceptual and result.perceptual.get("status") == "error"
    assert result.status == "passed"
    assert result.message == "Pixel threshold passed"
