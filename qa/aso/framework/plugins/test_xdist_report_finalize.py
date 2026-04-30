from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from framework.plugins import xdist_report_finalize as plugin

pytestmark = [pytest.mark.aso]


class _PluginManager:
    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled

    def hasplugin(self, name: str) -> bool:
        return name == "xdist" and self._enabled


def _config(
    *,
    xdist_enabled: bool = True,
    root: Path | None = None,
    args: tuple[str, ...] = (),
    collectonly: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        pluginmanager=_PluginManager(xdist_enabled),
        rootpath=root or Path("/repo"),
        option=SimpleNamespace(markexpr="", collectonly=collectonly),
        args=args,
    )


def test_is_xdist_controller_true_for_master_controller(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    config = _config(xdist_enabled=True)

    assert plugin._is_xdist_controller(config) is True


def test_is_xdist_controller_false_for_worker_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw2")
    config = _config(xdist_enabled=True)

    assert plugin._is_xdist_controller(config) is False


def test_is_xdist_controller_false_when_workerinput_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    config = _config(xdist_enabled=True)
    config.workerinput = {"run_id": "from-controller"}

    assert plugin._is_xdist_controller(config) is False


def test_ensure_shared_run_id_prefers_run_artifacts_run_id() -> None:
    config = _config()
    config._run_artifacts = SimpleNamespace(run_id="20260223_123000_000001")

    run_id = plugin._ensure_shared_run_id(config)

    assert run_id == "20260223_123000_000001"
    assert config._shared_run_id == run_id


def test_pytest_configure_node_sets_workerinput_run_id() -> None:
    config = _config()
    config._run_artifacts = SimpleNamespace(run_id="20260223_123000_000002")
    node = SimpleNamespace(config=config, workerinput={})

    plugin.pytest_configure_node(node)

    assert node.workerinput["run_id"] == "20260223_123000_000002"


def test_resolve_run_root_prefers_attached_run_artifacts(tmp_path: Path) -> None:
    run_root = tmp_path / "artifacts" / "20260223_123000_000003"
    config = _config(root=tmp_path)
    config._run_artifacts = SimpleNamespace(root=run_root)

    resolved = plugin._resolve_run_root(config)

    assert resolved == run_root


def test_merge_worker_durations_ignores_invalid_payloads(tmp_path: Path) -> None:
    run_root = tmp_path / "artifacts" / "run"
    logs = run_root / "logs"
    logs.mkdir(parents=True)
    (logs / "test_durations_gw0.json").write_text(
        json.dumps({"cases": {"a::test": 1.2, "b::test": "2.5"}}), encoding="utf-8"
    )
    (logs / "test_durations_gw1.json").write_text("not-json", encoding="utf-8")

    plugin._merge_worker_durations(run_root)

    merged = json.loads((logs / "test_durations.json").read_text(encoding="utf-8"))
    assert merged["cases"] == {"a::test": 1.2, "b::test": 2.5}


def test_merge_worker_test_data_ignores_invalid_payloads(tmp_path: Path) -> None:
    run_root = tmp_path / "artifacts" / "run"
    logs = run_root / "logs"
    logs.mkdir(parents=True)
    (logs / "test_data_gw0.json").write_text(
        json.dumps(
            {
                "cases": {
                    "a::test": {"auth_case": {"authenticated": True}},
                    "b::test": {"product": {"product_name": "Laptop"}},
                }
            }
        ),
        encoding="utf-8",
    )
    (logs / "test_data_gw1.json").write_text("not-json", encoding="utf-8")

    plugin._merge_worker_test_data(run_root)

    merged = json.loads((logs / "test_data.json").read_text(encoding="utf-8"))
    assert merged["cases"] == {
        "a::test": {"auth_case": {"authenticated": True}},
        "b::test": {"product": {"product_name": "Laptop"}},
    }


def test_load_merged_worker_visual_results_deduplicates_by_identity(tmp_path: Path) -> None:
    run_root = tmp_path / "artifacts" / "run"
    gw0 = run_root / "workers" / "gw0"
    gw1 = run_root / "workers" / "gw1"
    gw0.mkdir(parents=True)
    gw1.mkdir(parents=True)
    base_row = {
        "scenario_id": "hero-header",
        "viewport": "fhd",
        "browser": "chromium",
        "status": "passed",
        "compare_mode": "pixel",
        "baseline_path": "baseline.png",
        "actual_path": "actual.png",
        "diff_path": "diff.png",
        "heatmap_path": "heatmap.png",
        "suite_id": "suite",
        "pixel_changed_ratio": 0.01,
        "applied_shift_y": 2,
        "lpips": 0.02,
        "dists": 0.03,
        "thresholds": {"pixel_max": 0.1, "lpips_max": 0.2, "dists_max": 0.3, "shift_compensation_y_px": 6},
        "shift_compensation_y_px_effective": 6,
        "shift_compensation_y_px_env_default": 4,
        "shift_compensation_y_px_scenario_override": 6,
        "shift_compensation_y_px_source": "scenario_override",
        "message": "ok",
    }
    (gw0 / "visual_results.json").write_text(json.dumps({"results": [base_row]}), encoding="utf-8")
    updated = dict(base_row)
    updated["message"] = "newer"
    (gw1 / "visual_results.json").write_text(json.dumps({"results": [updated]}), encoding="utf-8")

    rows, file_count = plugin._load_merged_worker_visual_results(run_root)

    assert file_count == 2
    assert len(rows) == 1
    assert rows[0].message == "newer"
    assert rows[0].applied_shift_y == 2
    assert rows[0].shift_compensation_y_px_effective == 6
    assert rows[0].shift_compensation_y_px_env_default == 4
    assert rows[0].shift_compensation_y_px_scenario_override == 6
    assert rows[0].shift_compensation_y_px_source == "scenario_override"
    assert rows[0].thresholds is not None
    assert rows[0].thresholds.shift_compensation_y_px == 6


def test_pytest_sessionfinish_writes_visual_report_for_controller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root = tmp_path / "artifacts" / "20260223_123000_000004"
    logs = run_root / "logs"
    workers = run_root / "workers" / "gw0"
    logs.mkdir(parents=True)
    workers.mkdir(parents=True)
    (workers / "visual_results.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario_id": "hero-full",
                        "viewport": "fhd",
                        "browser": "chromium",
                        "status": "passed",
                        "compare_mode": "pixel",
                        "baseline_path": "b.png",
                        "actual_path": "a.png",
                        "diff_path": "d.png",
                        "heatmap_path": "h.png",
                        "suite_id": "suite",
                        "message": "ok",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    captured: dict[str, object] = {"write_calls": 0}

    def _fake_write_visual_report(report_dir: Path, results: list[object]) -> None:
        captured["report_dir"] = report_dir
        captured["results_len"] = len(results)
        captured["write_calls"] = int(captured.get("write_calls", 0)) + 1

    monkeypatch.setattr(plugin, "write_visual_report", _fake_write_visual_report)
    monkeypatch.setattr(plugin, "prepare_perceptual_placeholders", lambda **_kwargs: None)
    monkeypatch.setattr(plugin, "run_perceptual_postprocess", lambda **_kwargs: None)
    monkeypatch.setattr(plugin, "load_env", lambda: SimpleNamespace(pms_enabled=True))
    monkeypatch.setattr(plugin, "_ensure_run_metadata", lambda _root, _config: None)
    monkeypatch.setattr(plugin, "_merge_worker_durations", lambda _root: None)
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "master")

    config = _config(root=tmp_path)
    config._run_artifacts = SimpleNamespace(root=run_root)
    session = SimpleNamespace(config=config)

    plugin.pytest_sessionfinish(session, 0)

    assert captured["report_dir"] == run_root / "visual"
    assert captured["results_len"] == 1
    assert captured["write_calls"] == 2


def test_is_visual_profile_detects_visual_path_selection(tmp_path: Path) -> None:
    config = _config(root=tmp_path, args=("qa/visual",))

    assert plugin._is_visual_profile(config) is True


def test_pytest_sessionfinish_warns_for_visual_path_without_worker_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root = tmp_path / "artifacts" / "20260223_123000_000005"
    run_root.mkdir(parents=True)
    warnings: list[dict[str, object]] = []

    monkeypatch.setattr(plugin, "_ensure_run_metadata", lambda _root, _config: None)
    monkeypatch.setattr(plugin, "_merge_worker_durations", lambda _root: None)
    monkeypatch.setattr(
        plugin.logger, "warning", lambda message, **kwargs: warnings.append({"message": message, **kwargs})
    )
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "master")

    config = _config(root=tmp_path, args=("qa/visual",))
    config._run_artifacts = SimpleNamespace(root=run_root)
    session = SimpleNamespace(config=config)

    plugin.pytest_sessionfinish(session, 0)

    assert warnings == [
        {
            "message": "visual_worker_results_missing",
            "run_root": str(run_root),
            "workers_root": str(run_root / "workers"),
        }
    ]


def test_pytest_sessionfinish_skips_visual_warning_for_collect_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root = tmp_path / "artifacts" / "20260223_123000_000006"
    run_root.mkdir(parents=True)
    warnings: list[dict[str, object]] = []

    monkeypatch.setattr(
        plugin.logger, "warning", lambda message, **kwargs: warnings.append({"message": message, **kwargs})
    )
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "master")

    config = _config(root=tmp_path, args=("qa/visual",), collectonly=True)
    config._run_artifacts = SimpleNamespace(root=run_root)
    session = SimpleNamespace(config=config)

    plugin.pytest_sessionfinish(session, 0)

    assert warnings == []


def test_send_test_result_updates_uses_worker_payload_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_root = tmp_path / "artifacts" / "run"
    workers = run_root / "workers" / "gw0"
    workers.mkdir(parents=True)
    report_dir = run_root / "visual"
    report_dir.mkdir(parents=True)
    heatmap_rel = "heatmap/case-a.png"
    heatmap_file = report_dir / heatmap_rel
    heatmap_file.parent.mkdir(parents=True, exist_ok=True)
    heatmap_file.write_bytes(b"heat")
    nodeid = "qa/visual/test_sample.py::test_flow[a]"
    (workers / "test_result_payloads.json").write_text(
        json.dumps(
            {
                nodeid: {
                    "event_type": "test_result",
                    "run_uid": "run-uid-1",
                    "attempt": 1,
                    "nodeid": nodeid,
                    "test_id": nodeid,
                    "status": "passed",
                    "visual": {
                        "verdict": "analysis",
                        "execution": {"pms_usage_state": "deferred"},
                    },
                    "artifacts": [
                        {"kind": "trace", "path": "trace.zip", "available": True},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    class _Client:
        enabled = True

        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def test_result(self, payload: dict[str, object]) -> None:
            self.calls.append(payload)

    client = _Client()
    config = _config(root=tmp_path)
    config._run_uid = "run-uid-1"
    config._run_artifacts = SimpleNamespace(run_id="run")
    config._reporting_client = client

    monkeypatch.setattr(
        plugin,
        "load_env",
        lambda: SimpleNamespace(
            reporting_source_project="proj",
            framework_version="0.1.0",
            reporting_source_producer_id="",
            reporting_source_origin="local",
        ),
    )

    result = plugin.VisualResult(
        scenario_id="s-1",
        status="passed",
        message="ok",
        compare_mode="hybrid",
        baseline_path="b.png",
        actual_path="a.png",
        diff_path="d.png",
        heatmap_path=heatmap_rel,
        nodeid=nodeid,
    )
    result.applied_shift_y = 3
    result.shift_compensation_y_px_effective = 6
    result.shift_compensation_y_px_env_default = 4
    result.shift_compensation_y_px_scenario_override = 6
    result.shift_compensation_y_px_source = "scenario_override"
    plugin._send_test_result_updates(config, run_root, [result])

    assert len(client.calls) == 1
    payload = client.calls[0]
    payload = cast(dict[str, Any], payload)
    assert payload["attempt"] == 2
    assert payload["idempotency_key"] == f"test_result:run-uid-1:{nodeid}:2"
    visual = cast(dict[str, Any], payload["visual"])
    visual_scores = cast(dict[str, Any], visual["scores"])
    visual_execution = cast(dict[str, Any], visual["execution"])
    assert visual_scores["applied_shift_y"] == 3
    assert visual_scores["shift_compensation_y_px_effective"] == 6
    assert visual_execution["shift_compensation_y_px_env_default"] == 4
    assert visual_execution["shift_compensation_y_px_scenario_override"] == 6
    assert visual_execution["shift_compensation_y_px_source"] == "scenario_override"
    artifacts = cast(list[dict[str, Any]], payload["artifacts"])
    heatmap = next(item for item in artifacts if item.get("kind") == "visual_heatmap")
    assert heatmap["path"] == heatmap_rel
    assert heatmap["available"] is True
    assert heatmap["size_bytes"] == 4
    assert any(item.get("kind") == "trace" for item in artifacts)


def test_send_test_result_updates_marks_missing_heatmap_as_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root = tmp_path / "artifacts" / "run-missing"
    workers = run_root / "workers" / "gw0"
    workers.mkdir(parents=True)
    nodeid = "qa/visual/test_sample.py::test_flow[b]"
    heatmap_rel = "heatmap/missing.png"
    (workers / "test_result_payloads.json").write_text(
        json.dumps(
            {
                nodeid: {
                    "event_type": "test_result",
                    "run_uid": "run-uid-2",
                    "attempt": 1,
                    "nodeid": nodeid,
                    "test_id": nodeid,
                    "status": "passed",
                    "visual": {
                        "verdict": "analysis",
                        "execution": {"pms_usage_state": "deferred"},
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    class _Client:
        enabled = True

        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def test_result(self, payload: dict[str, object]) -> None:
            self.calls.append(payload)

    client = _Client()
    config = _config(root=tmp_path)
    config._run_uid = "run-uid-2"
    config._run_artifacts = SimpleNamespace(run_id="run-missing")
    config._reporting_client = client

    monkeypatch.setattr(
        plugin,
        "load_env",
        lambda: SimpleNamespace(
            reporting_source_project="proj",
            framework_version="0.1.0",
            reporting_source_producer_id="",
            reporting_source_origin="local",
        ),
    )

    result = plugin.VisualResult(
        scenario_id="s-2",
        status="passed",
        message="ok",
        compare_mode="hybrid",
        baseline_path="b.png",
        actual_path="a.png",
        diff_path="d.png",
        heatmap_path=heatmap_rel,
        nodeid=nodeid,
    )
    plugin._send_test_result_updates(config, run_root, [result])

    payload = client.calls[0]
    artifacts = cast(list[dict[str, Any]], payload["artifacts"])
    heatmap = next(item for item in artifacts if item.get("kind") == "visual_heatmap")
    assert heatmap["path"] == heatmap_rel
    assert heatmap["available"] is False
    assert heatmap["size_bytes"] == 0
    assert heatmap["sha256"] == ""


def test_send_test_result_updates_preserves_failed_dom_from_worker_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that failed_dom artifacts from worker payload survive update merge."""
    run_root = tmp_path / "artifacts" / "run-failed"
    workers = run_root / "workers" / "gw0"
    workers.mkdir(parents=True)
    report_dir = run_root / "visual"
    report_dir.mkdir(parents=True)
    heatmap_rel = "heatmap/case-failed.png"
    heatmap_file = report_dir / heatmap_rel
    heatmap_file.parent.mkdir(parents=True, exist_ok=True)
    heatmap_file.write_bytes(b"heat")

    nodeid = "qa/visual/test_failed.py::test_case[failed_with_dom]"
    (workers / "test_result_payloads.json").write_text(
        json.dumps(
            {
                nodeid: {
                    "event_type": "test_result",
                    "run_uid": "run-uid-failed",
                    "attempt": 1,
                    "nodeid": nodeid,
                    "test_id": nodeid,
                    "status": "failed",
                    "visual": {
                        "verdict": "analysis",
                        "execution": {"pms_usage_state": "deferred"},
                    },
                    "artifacts": [
                        {"kind": "trace", "path": "trace.zip", "available": True},
                        {
                            "kind": "failed_dom",
                            "path": "failed-dom/test_case.html",
                            "available": True,
                            "size_bytes": 245,
                        },
                        {"kind": "screenshot_raw", "path": "screenshots/test_raw.png", "available": True},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    class _Client:
        enabled = True

        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def test_result(self, payload: dict[str, object]) -> None:
            self.calls.append(payload)

    client = _Client()
    config = _config(root=tmp_path)
    config._run_uid = "run-uid-failed"
    config._run_artifacts = SimpleNamespace(run_id="run-failed")
    config._reporting_client = client

    monkeypatch.setattr(
        plugin,
        "load_env",
        lambda: SimpleNamespace(
            reporting_source_project="proj",
            framework_version="0.1.0",
            reporting_source_producer_id="",
            reporting_source_origin="local",
        ),
    )

    result = plugin.VisualResult(
        scenario_id="s-failed",
        status="failed",
        message="visual comparison failed",
        compare_mode="hybrid",
        baseline_path="b.png",
        actual_path="a.png",
        diff_path="d.png",
        heatmap_path=heatmap_rel,
        nodeid=nodeid,
    )
    result.pixel_changed_ratio = 0.05
    result.lpips = 0.2
    result.dists = 0.15
    plugin._send_test_result_updates(config, run_root, [result])

    assert len(client.calls) == 1
    payload = cast(dict[str, Any], client.calls[0])
    assert payload["attempt"] == 2
    artifacts = cast(list[dict[str, Any]], payload["artifacts"])

    # Verify that failed_dom artifact from worker payload is preserved
    failed_dom_artifacts = [item for item in artifacts if item.get("kind") == "failed_dom"]
    assert len(failed_dom_artifacts) == 1
    failed_dom = failed_dom_artifacts[0]
    assert failed_dom["path"] == "failed-dom/test_case.html"
    assert failed_dom["available"] is True
    assert failed_dom["size_bytes"] == 245

    # Verify that other worker artifacts are also preserved
    assert any(item.get("kind") == "trace" for item in artifacts)
    assert any(item.get("kind") == "screenshot_raw" for item in artifacts)

    # Verify that visual heatmap is added
    heatmap_artifacts = [item for item in artifacts if item.get("kind") == "visual_heatmap"]
    assert len(heatmap_artifacts) == 1
    assert heatmap_artifacts[0]["path"] == heatmap_rel
