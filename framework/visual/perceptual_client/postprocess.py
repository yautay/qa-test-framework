from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from framework.env import RuntimeEnv
from framework.visual.models import VisualResult

from .ids import build_job_id, build_pair_id, build_test_id
from .pms_client import PMSClient, PMSClientError


@dataclass
class _RateLimiter:
    rps: float
    _next_at: float = 0.0

    def wait(self) -> None:
        if self.rps <= 0:
            return
        now = time.monotonic()
        if self._next_at > now:
            time.sleep(self._next_at - now)
        step = 1.0 / self.rps
        self._next_at = max(self._next_at + step, time.monotonic() + step)


@dataclass
class _PairJob:
    result: VisualResult
    pair_id: str
    job_id: str
    submitted_at: float
    status: str


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_rel_visual_path(path: Path, report_dir: Path) -> str:
    try:
        return path.resolve().relative_to(report_dir.resolve()).as_posix()
    except Exception:
        return path.name


def _sanitize_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in str(value or "").strip())
    return cleaned[:200] or "heatmap"


def _upsert_perceptual(result: VisualResult, payload: dict[str, Any]) -> None:
    result.perceptual = payload
    if not isinstance(result.test_metadata, dict):
        result.test_metadata = {}
    result.test_metadata["perceptual"] = payload


def _expects_perceptual(result: VisualResult) -> bool:
    return str(getattr(result, "compare_mode", "") or "").strip().lower() in {"perceptual", "hybrid"}


def _mark_global_skip(results: list[VisualResult], reason: str) -> int:
    affected = 0
    for result in results:
        if not _expects_perceptual(result):
            continue
        affected += 1
        _upsert_perceptual(
            result,
            {
                "status": "skipped",
                "lpips": None,
                "dists": None,
                "heatmap": None,
                "job_id": None,
                "timing_ms": 0,
                "error_message": reason,
            },
        )
    return affected


def _log_perceptual_coverage(*, run_id: str, results: list[VisualResult]) -> None:
    eligible = 0
    with_status = 0
    missing_scores = 0
    status_counts: dict[str, int] = {}

    for result in results:
        if not _expects_perceptual(result):
            continue
        eligible += 1
        payload = result.perceptual if isinstance(result.perceptual, dict) else None
        if payload is None and isinstance(result.test_metadata, dict):
            nested = result.test_metadata.get("perceptual")
            if isinstance(nested, dict):
                payload = nested
        if payload is not None:
            with_status += 1
            status = str(payload.get("status") or "unknown").strip().lower() or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
        if result.lpips is None and result.dists is None:
            missing_scores += 1

    logger.info(
        "perceptual_postprocess_coverage",
        run_id=run_id,
        eligible=eligible,
        with_status=with_status,
        missing_scores=missing_scores,
        status_counts=status_counts,
    )


def run_perceptual_postprocess(
    *,
    env: RuntimeEnv,
    run_id: str,
    report_dir: Path,
    results: list[VisualResult],
) -> None:
    if not results:
        logger.info("perceptual_postprocess_skipped", run_id=run_id, reason="empty_results")
        return

    if not env.pms_enabled:
        logger.info("perceptual_postprocess_skipped", run_id=run_id, reason="pms_disabled")
        return

    client = PMSClient(
        base_url=env.pms_base_url,
        timeout_seconds=env.pms_timeout_sec,
        health_timeout_seconds=env.pms_health_timeout_seconds,
        retry_max=env.pms_retry_max,
    )

    if not client.enabled:
        msg = "PMS is enabled but PMS_BASE_URL is empty"
        if env.pms_required:
            raise PMSClientError(msg)
        affected = _mark_global_skip(results, msg)
        logger.error(
            "perceptual_postprocess_unavailable",
            run_id=run_id,
            reason=msg,
            action="skip_perceptual_postprocess",
            affected_pairs=affected,
        )
        _log_perceptual_coverage(run_id=run_id, results=results)
        return

    if not client.health():
        msg = "PMS healthcheck failed; skipping perceptual postprocess"
        if env.pms_required:
            raise PMSClientError(msg)
        affected = _mark_global_skip(results, msg)
        logger.error(
            "perceptual_postprocess_unavailable",
            run_id=run_id,
            reason=msg,
            action="skip_perceptual_postprocess",
            affected_pairs=affected,
        )
        _log_perceptual_coverage(run_id=run_id, results=results)
        return

    submit_limit = _RateLimiter(rps=max(0.0, float(env.pms_submit_rps)))
    poll_limit = _RateLimiter(rps=max(0.0, float(env.pms_poll_rps)))
    timeout_sec = max(1, int(env.pms_timeout_sec))
    max_inflight = max(1, int(env.pms_max_inflight))
    server_active_limit = max(1, int(env.pms_server_active_limit))

    heatmaps_dir = report_dir / "heatmaps"
    inflight: dict[str, _PairJob] = {}
    pending: list[_PairJob] = []
    done_count = 0
    error_count = 0

    started_at = time.monotonic()
    for result in results:
        baseline = Path(str(result.baseline_path or "").strip())
        actual = Path(str(result.actual_path or "").strip())
        if not baseline.is_file() or not actual.is_file():
            _upsert_perceptual(
                result,
                {
                    "status": "skipped",
                    "lpips": None,
                    "dists": None,
                    "heatmap": None,
                    "job_id": None,
                    "timing_ms": 0,
                    "error_message": "missing baseline/actual pair",
                },
            )
            continue

        test_id = build_test_id(
            suite_id=result.suite_id,
            scenario_id=result.scenario_id,
            viewport=result.viewport,
            browser=result.browser,
        )
        pair_id = build_pair_id(test_id=test_id, baseline_path=str(baseline), actual_path=str(actual))
        job_id = build_job_id(
            run_id=run_id,
            pair_id=pair_id,
            metric=env.pms_metric,
            model=env.pms_model,
            normalize=env.pms_normalize,
        )
        pending.append(
            result_job := _PairJob(result=result, pair_id=pair_id, job_id=job_id, submitted_at=0.0, status="pending")
        )
        _upsert_perceptual(
            result,
            {
                "status": "queued",
                "lpips": None,
                "dists": None,
                "heatmap": None,
                "job_id": job_id,
                "timing_ms": 0,
                "error_message": None,
            },
        )
        logger.debug("perceptual_pair_queued", run_id=run_id, pair_id=pair_id, job_id=job_id)

    logger.info(
        "perceptual_postprocess_started",
        run_id=run_id,
        total_results=len(results),
        queued_pairs=len(pending),
        metric=env.pms_metric,
        model=env.pms_model,
        normalize=env.pms_normalize,
    )

    while pending or inflight:
        if pending and len(inflight) < max_inflight:
            server_active = 0
            try:
                poll_limit.wait()
                jobs = client.list_jobs()
                server_active = sum(1 for j in jobs if str(j.get("status", "")).lower() in {"queued", "running"})
                logger.debug(
                    "perceptual_server_queue_snapshot",
                    run_id=run_id,
                    server_active=server_active,
                    server_active_limit=server_active_limit,
                )
            except PMSClientError as exc:
                logger.warning("perceptual_server_queue_snapshot_failed", run_id=run_id, error=str(exc))

            if server_active < server_active_limit:
                next_job = pending.pop(0)
                submit_limit.wait()
                baseline = Path(str(next_job.result.baseline_path))
                actual = Path(str(next_job.result.actual_path))
                try:
                    client.submit_job(
                        job_id=next_job.job_id,
                        pair_id=next_job.pair_id,
                        metric=env.pms_metric,
                        model=env.pms_model,
                        normalize=env.pms_normalize,
                        img_a=baseline,
                        img_b=actual,
                    )
                    next_job.submitted_at = time.monotonic()
                    next_job.status = "submitted"
                    inflight[next_job.job_id] = next_job
                    logger.info(
                        "perceptual_job_submitted",
                        run_id=run_id,
                        pair_id=next_job.pair_id,
                        job_id=next_job.job_id,
                        inflight=len(inflight),
                        pending=len(pending),
                    )
                except PMSClientError as exc:
                    error_count += 1
                    next_job.status = "error"
                    _upsert_perceptual(
                        next_job.result,
                        {
                            "status": "error",
                            "lpips": None,
                            "dists": None,
                            "heatmap": None,
                            "job_id": next_job.job_id,
                            "timing_ms": 0,
                            "error_message": str(exc),
                        },
                    )
                    logger.error(
                        "perceptual_job_submit_failed",
                        run_id=run_id,
                        pair_id=next_job.pair_id,
                        job_id=next_job.job_id,
                        error=str(exc),
                    )

        for job_id, item in list(inflight.items()):
            poll_limit.wait()
            elapsed = max(0.0, time.monotonic() - item.submitted_at)
            if elapsed > timeout_sec:
                error_count += 1
                inflight.pop(job_id, None)
                _upsert_perceptual(
                    item.result,
                    {
                        "status": "timeout",
                        "lpips": None,
                        "dists": None,
                        "heatmap": None,
                        "job_id": item.job_id,
                        "timing_ms": int(elapsed * 1000),
                        "error_message": f"timeout after {timeout_sec}s",
                    },
                )
                logger.error("perceptual_job_timeout", run_id=run_id, pair_id=item.pair_id, job_id=item.job_id)
                continue

            try:
                payload = client.get_job(job_id)
            except PMSClientError as exc:
                logger.warning(
                    "perceptual_job_poll_failed",
                    run_id=run_id,
                    pair_id=item.pair_id,
                    job_id=item.job_id,
                    error=str(exc),
                )
                continue

            status = str(payload.get("status", "")).strip().lower()
            if status in {"queued", "running"}:
                logger.debug(
                    "perceptual_job_waiting", run_id=run_id, pair_id=item.pair_id, job_id=item.job_id, status=status
                )
                continue

            timing_ms = int(max(0.0, time.monotonic() - item.submitted_at) * 1000)
            inflight.pop(job_id, None)

            if status == "done":
                done_count += 1
                lpips = _to_float(payload.get("lpips"))
                dists = _to_float(payload.get("dists"))

                heatmap_rel: str | None = None
                if env.pms_metric in {"lpips", "both"}:
                    file_stem = _sanitize_name(item.pair_id)
                    heatmap_path = heatmaps_dir / f"{file_stem}.png"
                    if client.download_heatmap(item.job_id, heatmap_path):
                        heatmap_rel = _to_rel_visual_path(heatmap_path, report_dir)

                item.result.lpips = lpips
                item.result.dists = dists
                item.result.heatmap_path = heatmap_rel or ""
                _upsert_perceptual(
                    item.result,
                    {
                        "status": "done",
                        "lpips": lpips,
                        "dists": dists,
                        "heatmap": heatmap_rel,
                        "job_id": item.job_id,
                        "timing_ms": timing_ms,
                        "error_message": None,
                    },
                )
                logger.info(
                    "perceptual_job_done",
                    run_id=run_id,
                    pair_id=item.pair_id,
                    job_id=item.job_id,
                    lpips=lpips,
                    dists=dists,
                    heatmap=heatmap_rel,
                    timing_ms=timing_ms,
                )
                continue

            error_count += 1
            err_message = str(payload.get("error") or payload.get("message") or f"status={status}")
            _upsert_perceptual(
                item.result,
                {
                    "status": "error",
                    "lpips": None,
                    "dists": None,
                    "heatmap": None,
                    "job_id": item.job_id,
                    "timing_ms": timing_ms,
                    "error_message": err_message,
                },
            )
            logger.error(
                "perceptual_job_failed",
                run_id=run_id,
                pair_id=item.pair_id,
                job_id=item.job_id,
                status=status,
                error=err_message,
            )

        if inflight:
            interval = max(100, int(env.pms_poll_interval_ms)) / 1000.0
            time.sleep(interval)

    took_ms = int((time.monotonic() - started_at) * 1000)
    logger.info(
        "perceptual_postprocess_finished",
        run_id=run_id,
        total=len(results),
        done=done_count,
        errors=error_count,
        took_ms=took_ms,
    )
    _log_perceptual_coverage(run_id=run_id, results=results)
