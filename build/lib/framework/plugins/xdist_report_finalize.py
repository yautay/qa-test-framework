from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest
from loguru import logger

import settings_cli
from framework.artifacts import resolve_artifacts_base_dir
from framework.env import load_env
from framework.visual.models import VisualResult, VisualThresholds
from framework.visual.perceptual_client import prepare_perceptual_placeholders, run_perceptual_postprocess
from framework.visual.report_builder import write_visual_report, write_visual_results_json


def _is_xdist_controller(config: pytest.Config) -> bool:
    worker_id = str(os.getenv("PYTEST_XDIST_WORKER") or "").strip()
    if worker_id and worker_id != "master":
        return False
    if hasattr(config, "workerinput"):
        return False
    return bool(config.pluginmanager.hasplugin("xdist"))


def _ensure_shared_run_id(config: pytest.Config) -> str:
    token = str(getattr(config, "_shared_run_id", "") or "").strip()
    if token:
        return token

    run_artifacts = getattr(config, "_run_artifacts", None)
    token = str(getattr(run_artifacts, "run_id", "") or "").strip()
    if token:
        config._shared_run_id = token
        return token

    token = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    config._shared_run_id = token
    return token


def pytest_configure(config: pytest.Config) -> None:
    if not _is_xdist_controller(config):
        return
    _ensure_shared_run_id(config)


def pytest_configure_node(node) -> None:
    node.workerinput["run_id"] = _ensure_shared_run_id(node.config)


def _resolve_run_root(config: pytest.Config) -> Path | None:
    run_artifacts = getattr(config, "_run_artifacts", None)
    if run_artifacts is not None:
        root = getattr(run_artifacts, "root", None)
        if isinstance(root, Path):
            return root

    run_id = str(getattr(config, "_shared_run_id", "") or "").strip()
    if not run_id:
        worker_input = getattr(config, "workerinput", None)
        if isinstance(worker_input, dict):
            run_id = str(worker_input.get("run_id") or "").strip()
    if not run_id:
        return None

    env = load_env()
    artifacts_base_dir = resolve_artifacts_base_dir(env.artifacts_dir, config.rootpath)
    return (artifacts_base_dir / run_id).resolve()


def _ensure_run_metadata(run_root: Path, config: pytest.Config) -> None:
    target = run_root / "run-metadata.json"
    if target.exists():
        return

    metadata = getattr(config, "_run_metadata", None)
    tester = ""
    run_note = ""
    if isinstance(metadata, dict):
        tester = str(metadata.get("tester", "") or "")
        run_note = str(metadata.get("run_note", "") or "")
    else:
        tester = str(getattr(settings_cli, "tester", "") or "")
        run_note = str(getattr(settings_cli, "run_note", "") or "")

    payload = {"tester": tester, "run_note": run_note}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _merge_worker_durations(run_root: Path) -> None:
    logs_dir = run_root / "logs"
    files = sorted(logs_dir.glob("test_durations_*.json"))
    if not files:
        return

    merged: dict[str, float] = {}
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        cases = payload.get("cases", {}) if isinstance(payload, dict) else {}
        if not isinstance(cases, dict):
            continue
        for nodeid, seconds in cases.items():
            if not isinstance(nodeid, str):
                continue
            try:
                merged[nodeid] = float(seconds)
            except (TypeError, ValueError):
                continue

    out = {"cases": dict(sorted(merged.items()))}
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "test_durations.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


def _result_from_dict(data: dict[str, object]) -> VisualResult | None:
    try:
        status_raw = str(data.get("status") or "failed")
        compare_mode_raw = str(data.get("compare_mode") or "pixel")
        if status_raw not in {
            "passed",
            "failed",
            "skipped",
            "new",
            "uncertain",
            "analysis",
        }:
            status_raw = "failed"
        if compare_mode_raw not in {"pixel", "hybrid"}:
            compare_mode_raw = "pixel"

        thresholds_raw_obj = data.get("thresholds")
        thresholds_raw = thresholds_raw_obj if isinstance(thresholds_raw_obj, dict) else None
        thresholds = None
        if thresholds_raw is not None:
            pixel_uncertain_delta = thresholds_raw.get("pixel_uncertain_delta")
            lpips_uncertain_delta = thresholds_raw.get("lpips_uncertain_delta")
            dists_uncertain_delta = thresholds_raw.get("dists_uncertain_delta")
            thresholds = VisualThresholds(
                pixel_max=float(thresholds_raw.get("pixel_max", 0.0)),
                lpips_max=float(thresholds_raw.get("lpips_max", 0.0)),
                dists_max=float(thresholds_raw.get("dists_max", 0.0)),
                pixel_uncertain_delta=float(cast(Any, pixel_uncertain_delta))
                if pixel_uncertain_delta is not None
                else None,
                lpips_uncertain_delta=float(cast(Any, lpips_uncertain_delta))
                if lpips_uncertain_delta is not None
                else None,
                dists_uncertain_delta=float(cast(Any, dists_uncertain_delta))
                if dists_uncertain_delta is not None
                else None,
            )

        pixel_changed_ratio_raw = data.get("pixel_changed_ratio")
        lpips_raw = data.get("lpips")
        dists_raw = data.get("dists")
        test_metadata_obj = data.get("test_metadata")
        perceptual_obj = data.get("perceptual")
        test_metadata = test_metadata_obj if isinstance(test_metadata_obj, dict) else None
        if isinstance(perceptual_obj, dict):
            if test_metadata is None:
                test_metadata = {}
            test_metadata["perceptual"] = perceptual_obj

        return VisualResult(
            scenario_id=str(data.get("scenario_id") or ""),
            status=cast(Any, status_raw),
            message=str(data.get("message") or ""),
            compare_mode=cast(Any, compare_mode_raw),
            baseline_path=str(data.get("baseline_path") or ""),
            actual_path=str(data.get("actual_path") or ""),
            diff_path=str(data.get("diff_path") or ""),
            heatmap_path=str(data.get("heatmap_path") or ""),
            suite_id=str(data.get("suite_id") or ""),
            viewport=str(data.get("viewport") or ""),
            browser=str(data.get("browser") or ""),
            pixel_changed_ratio=float(cast(Any, pixel_changed_ratio_raw))
            if pixel_changed_ratio_raw is not None
            else None,
            lpips=float(cast(Any, lpips_raw)) if lpips_raw is not None else None,
            dists=float(cast(Any, dists_raw)) if dists_raw is not None else None,
            thresholds=thresholds,
            tester=str(data.get("tester") or ""),
            run_note=str(data.get("run_note") or ""),
            test_metadata=test_metadata,
            perceptual=perceptual_obj if isinstance(perceptual_obj, dict) else None,
        )
    except (TypeError, ValueError):
        return None


def _load_merged_worker_visual_results(run_root: Path) -> tuple[list[VisualResult], int]:
    workers_root = run_root / "workers"
    worker_files = sorted(workers_root.glob("*/visual_results.json"))
    if not worker_files:
        return [], 0

    merged: dict[tuple[str, str, str], VisualResult] = {}
    for path in worker_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        rows = payload.get("results", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            result = _result_from_dict(row)
            if result is None:
                continue
            key = (result.scenario_id, result.viewport, result.browser)
            merged[key] = result
    return list(merged.values()), len(worker_files)


def _is_visual_profile(config: pytest.Config) -> bool:
    markexpr = str(getattr(config.option, "markexpr", "") or "").strip()
    return markexpr == "visual"


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _ = exitstatus
    config = session.config
    if not _is_xdist_controller(config):
        return

    run_root = _resolve_run_root(config)
    if run_root is None:
        return

    _ensure_run_metadata(run_root, config)
    _merge_worker_durations(run_root)

    merged_results, worker_visual_files = _load_merged_worker_visual_results(run_root)
    if worker_visual_files == 0:
        if _is_visual_profile(config):
            logger.warning(
                "visual_worker_results_missing",
                run_root=str(run_root),
                workers_root=str(run_root / "workers"),
            )
        return

    env = load_env()
    report_dir = run_root / "visual"
    prepare_perceptual_placeholders(
        env=env,
        run_id=str(run_root.name),
        report_dir=report_dir,
        results=merged_results,
    )

    try:
        write_visual_report(report_dir, merged_results)
    except Exception as exc:
        logger.warning("visual_report_finalize_failed", run_root=str(run_root), error=str(exc))

    if env.pms_enabled:
        try:
            run_perceptual_postprocess(
                env=env,
                run_id=str(run_root.name),
                report_dir=report_dir,
                results=merged_results,
                on_results_updated=lambda: write_visual_results_json(report_dir, merged_results),
            )
        except Exception as exc:
            logger.warning("perceptual_postprocess_failed", run_root=str(run_root), error=str(exc))

        try:
            write_visual_report(report_dir, merged_results)
        except Exception as exc:
            logger.warning("visual_report_finalize_failed", run_root=str(run_root), error=str(exc))
