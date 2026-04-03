from __future__ import annotations

import hashlib
import json
import os
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from loguru import logger

import settings_cli
from framework.artifacts import resolve_artifacts_base_dir
from framework.env import load_env
from framework.visual.build_metadata import build_visual_build_metadata, write_visual_build_metadata
from framework.visual.models import VisualResult, VisualThresholds
from framework.visual.perceptual import prepare_perceptual_placeholders, run_perceptual_postprocess
from framework.visual.report_builder import write_visual_report, write_visual_results_json

_VISUAL_RESULT_ARTIFACT_KINDS = {
    "visual_baseline": "baseline_path",
    "visual_actual": "actual_path",
    "visual_diff": "diff_path",
    "visual_heatmap": "heatmap_path",
}


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

    token = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
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
    payload: dict[str, Any]
    if isinstance(metadata, dict):
        payload = dict(metadata)
    else:
        payload = {
            "tester": str(getattr(settings_cli, "tester", "") or ""),
            "run_note": str(getattr(settings_cli, "run_note", "") or ""),
        }
    payload["tester"] = str(payload.get("tester", "") or "")
    payload["run_note"] = str(payload.get("run_note", "") or "")
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
                pixel_uncertain_delta=(
                    float(cast(Any, pixel_uncertain_delta)) if pixel_uncertain_delta is not None else None
                ),
                lpips_uncertain_delta=(
                    float(cast(Any, lpips_uncertain_delta)) if lpips_uncertain_delta is not None else None
                ),
                dists_uncertain_delta=(
                    float(cast(Any, dists_uncertain_delta)) if dists_uncertain_delta is not None else None
                ),
                shift_compensation_y_px=(
                    int(cast(Any, thresholds_raw.get("shift_compensation_y_px")))
                    if thresholds_raw.get("shift_compensation_y_px") is not None
                    else None
                ),
            )

        pixel_changed_ratio_raw = data.get("pixel_changed_ratio")
        applied_shift_y_raw = data.get("applied_shift_y")
        shift_effective_raw = data.get("shift_compensation_y_px_effective")
        shift_env_default_raw = data.get("shift_compensation_y_px_env_default")
        shift_scenario_override_raw = data.get("shift_compensation_y_px_scenario_override")
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
            comparison_baseline_path=str(data.get("comparison_baseline_path") or ""),
            comparison_actual_path=str(data.get("comparison_actual_path") or ""),
            heatmap_path=str(data.get("heatmap_path") or ""),
            suite_id=str(data.get("suite_id") or ""),
            viewport=str(data.get("viewport") or ""),
            browser=str(data.get("browser") or ""),
            nodeid=str(data.get("nodeid") or ""),
            pixel_changed_ratio=(
                float(cast(Any, pixel_changed_ratio_raw)) if pixel_changed_ratio_raw is not None else None
            ),
            applied_shift_y=int(cast(Any, applied_shift_y_raw)) if applied_shift_y_raw is not None else None,
            shift_compensation_y_px_effective=(
                int(cast(Any, shift_effective_raw)) if shift_effective_raw is not None else None
            ),
            shift_compensation_y_px_env_default=(
                int(cast(Any, shift_env_default_raw)) if shift_env_default_raw is not None else None
            ),
            shift_compensation_y_px_scenario_override=(
                int(cast(Any, shift_scenario_override_raw)) if shift_scenario_override_raw is not None else None
            ),
            shift_compensation_y_px_source=(str(data.get("shift_compensation_y_px_source") or "") or None),
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


def _load_worker_test_result_payloads(run_root: Path) -> dict[str, dict[str, Any]]:
    workers_root = run_root / "workers"
    payload_files = sorted(workers_root.glob("*/test_result_payloads.json"))
    merged: dict[str, dict[str, Any]] = {}
    for path in payload_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        for nodeid, item in payload.items():
            if not isinstance(nodeid, str) or not nodeid.strip():
                continue
            if not isinstance(item, dict):
                continue
            merged[nodeid] = cast(dict[str, Any], item)
    return merged


def _build_source_context(env, worker_id: str) -> dict[str, str]:
    host = socket.gethostname()
    user = os.getenv("USER") or os.getenv("USERNAME") or ""
    instance_id = f"{host}-{user}-{os.getpid()}"
    producer_id = str(getattr(env, "reporting_source_producer_id", "") or "").strip() or host
    return {
        "project": str(getattr(env, "reporting_source_project", "") or ""),
        "framework_version": str(getattr(env, "framework_version", "") or "unknown"),
        "producer_id": producer_id,
        "instance_id": instance_id,
        "host": host,
        "user": user,
        "worker_id": worker_id,
        "origin": str(getattr(env, "reporting_source_origin", "") or "local"),
    }


def _build_test_result_idempotency_key(run_uid: str, nodeid: str, attempt: int) -> str:
    return f"test_result:{run_uid}:{nodeid}:{int(attempt)}"


def _sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _build_artifact_entry(kind: str, raw_path: str, report_dir: Path) -> dict[str, Any]:
    path_token = str(raw_path or "").strip()
    available = False
    size_bytes = 0
    size_mib = 0.0
    sha256 = ""
    if path_token:
        artifact_path = Path(path_token)
        if not artifact_path.is_absolute():
            artifact_path = report_dir / artifact_path
        if artifact_path.is_file():
            available = True
            try:
                size_bytes = int(artifact_path.stat().st_size)
                size_mib = round(size_bytes / (1024 * 1024), 3)
            except OSError:
                size_bytes = 0
                size_mib = 0.0
            try:
                sha256 = _sha256_for_file(artifact_path)
            except OSError:
                sha256 = ""
    return {
        "kind": kind,
        "path": path_token,
        "uri": "",
        "sha256": sha256,
        "size_bytes": size_bytes,
        "size_mib": size_mib,
        "available": available,
    }


def _merge_visual_result_artifacts(
    existing_artifacts: Any,
    result: VisualResult,
    report_dir: Path,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    if isinstance(existing_artifacts, list):
        for item in existing_artifacts:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip()
            if kind in _VISUAL_RESULT_ARTIFACT_KINDS:
                continue
            merged.append(dict(item))
    for kind, attr_name in _VISUAL_RESULT_ARTIFACT_KINDS.items():
        merged.append(_build_artifact_entry(kind, str(getattr(result, attr_name, "") or ""), report_dir))
    return merged


def _build_visual_payload_from_result(result: VisualResult, existing_visual: Any) -> dict[str, Any]:
    thresholds = getattr(result, "thresholds", None)
    execution = {}
    shift_effective = getattr(result, "shift_compensation_y_px_effective", None)
    shift_env_default = getattr(result, "shift_compensation_y_px_env_default", None)
    shift_scenario_override = getattr(result, "shift_compensation_y_px_scenario_override", None)
    shift_source = getattr(result, "shift_compensation_y_px_source", None)
    metadata = getattr(result, "test_metadata", None)
    if isinstance(metadata, dict):
        scores_meta = metadata.get("scores")
        if shift_effective is None and isinstance(scores_meta, dict):
            value = scores_meta.get("shift_compensation_y_px_effective")
            if value is not None:
                shift_effective = value
        execution_meta = metadata.get("execution")
        if isinstance(execution_meta, dict):
            if shift_env_default is None:
                value = execution_meta.get("shift_compensation_y_px_env_default")
                if value is not None:
                    shift_env_default = value
            if shift_scenario_override is None:
                value = execution_meta.get("shift_compensation_y_px_scenario_override")
                if value is not None:
                    shift_scenario_override = value
            if not shift_source:
                value = execution_meta.get("shift_compensation_y_px_source")
                if value:
                    shift_source = value
    if isinstance(existing_visual, dict):
        execution_value = existing_visual.get("execution")
        if isinstance(execution_value, dict):
            execution = dict(execution_value)
    execution["shift_compensation_y_px_env_default"] = (
        int(cast(Any, shift_env_default)) if shift_env_default is not None else None
    )
    execution["shift_compensation_y_px_scenario_override"] = (
        int(cast(Any, shift_scenario_override)) if shift_scenario_override is not None else None
    )
    execution["shift_compensation_y_px_effective"] = (
        int(cast(Any, shift_effective)) if shift_effective is not None else None
    )
    execution["shift_compensation_y_px_source"] = str(shift_source or "") or None
    return {
        "threshold_scope": "scenario+viewport+browser",
        "thresholds_used": {
            "pixel_max": thresholds.pixel_max if thresholds else None,
            "lpips_max": thresholds.lpips_max if thresholds else None,
            "dists_max": thresholds.dists_max if thresholds else None,
            "shift_compensation_y_px": thresholds.shift_compensation_y_px if thresholds else None,
        },
        "scores": {
            "pixel_changed_ratio": result.pixel_changed_ratio,
            "applied_shift_y": result.applied_shift_y,
            "shift_compensation_y_px_effective": (
                int(cast(Any, shift_effective)) if shift_effective is not None else None
            ),
            "lpips": result.lpips,
            "dists": result.dists,
        },
        "execution": execution,
        "verdict": result.status,
    }


def _send_test_result_updates(config: pytest.Config, run_root: Path, results: list[VisualResult]) -> None:
    reporting_client = getattr(config, "_reporting_client", None)
    if reporting_client is None or not bool(getattr(reporting_client, "enabled", False)):
        return

    payloads_by_nodeid = _load_worker_test_result_payloads(run_root)
    if not payloads_by_nodeid:
        return

    env = load_env()
    run_artifacts = getattr(config, "_run_artifacts", None)
    run_id = str(getattr(run_artifacts, "run_id", "") or run_root.name)
    run_uid = str(getattr(config, "_run_uid", "") or os.getenv("PYTEST_XDIST_RUN_UID", "") or "")
    if not run_uid:
        return

    run_metadata_path = run_root / "run-metadata.json"
    run_metadata: dict[str, Any] = {"tester": "", "run_note": ""}
    if run_metadata_path.is_file():
        try:
            payload = json.loads(run_metadata_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                run_metadata = dict(payload)
                run_metadata["tester"] = str(run_metadata.get("tester", "") or "")
                run_metadata["run_note"] = str(run_metadata.get("run_note", "") or "")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass

    worker_id = os.getenv("PYTEST_XDIST_WORKER", "master")
    report_dir = run_root / "visual"
    source = _build_source_context(env, worker_id)
    for result in results:
        nodeid = str(getattr(result, "nodeid", "") or "").strip()
        if not nodeid:
            continue
        base_payload = payloads_by_nodeid.get(nodeid)
        if not isinstance(base_payload, dict):
            continue
        base_visual = base_payload.get("visual")
        if not isinstance(base_visual, dict) or str(base_visual.get("verdict", "")).strip().lower() != "analysis":
            continue
        if str(getattr(result, "status", "") or "").strip().lower() == "analysis":
            continue

        update = dict(base_payload)
        attempt = 2
        update["event_id"] = str(uuid.uuid4())
        update["event_type"] = "test_result"
        update["event_time_utc"] = datetime.now(UTC).isoformat()
        update["run_id"] = run_id
        update["run_uid"] = run_uid
        update["source"] = source
        metadata = base_payload.get("metadata")
        metadata_out = dict(metadata) if isinstance(metadata, dict) else dict(run_metadata)
        metadata_out["update_reason"] = "pms_postprocess_finalized"
        update["metadata"] = metadata_out
        update["attempt"] = attempt
        update["idempotency_key"] = _build_test_result_idempotency_key(run_uid, nodeid, attempt)
        update["test_id"] = nodeid
        update["nodeid"] = nodeid
        update["status"] = str(getattr(result, "status", "") or base_payload.get("status", "failed"))
        update["visual"] = _build_visual_payload_from_result(result, base_visual)
        update["artifacts"] = _merge_visual_result_artifacts(base_payload.get("artifacts"), result, report_dir)

        logger.info("reporting_test_result_update", run_id=run_id, nodeid=nodeid, status=update["status"])
        reporting_client.test_result(update)


def _is_visual_profile(config: pytest.Config) -> bool:
    markexpr = str(getattr(config.option, "markexpr", "") or "").strip()
    if "visual" in markexpr:
        return True

    root = Path(str(config.rootpath)).resolve()
    visual_root = (root / "qa" / "visual").resolve()
    raw_args = cast(tuple[Any, ...], tuple(getattr(config, "args", ()) or ()))
    for raw in raw_args:
        token = str(raw or "").strip()
        if not token or token.startswith("-"):
            continue
        token_path = token.split("::", 1)[0]
        candidate = Path(token_path)
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if candidate == visual_root or visual_root in candidate.parents:
            return True
    return False


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _ = exitstatus
    config = session.config
    if bool(getattr(config.option, "collectonly", False)):
        return
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
    payloads_by_nodeid = _load_worker_test_result_payloads(run_root)
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
    metadata = build_visual_build_metadata(results=merged_results, payloads_by_nodeid=payloads_by_nodeid)
    write_visual_build_metadata(report_dir, metadata)

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
            _send_test_result_updates(config, run_root, merged_results)
        except Exception as exc:
            logger.warning("reporting_test_result_updates_failed", run_root=str(run_root), error=str(exc))

        try:
            write_visual_report(report_dir, merged_results)
        except Exception as exc:
            logger.warning("visual_report_finalize_failed", run_root=str(run_root), error=str(exc))
        metadata = build_visual_build_metadata(results=merged_results, payloads_by_nodeid=payloads_by_nodeid)
        write_visual_build_metadata(report_dir, metadata)
