from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from framework.visual.models import VisualResult
from qa.visual import conftest as visual_conftest

pytestmark = [pytest.mark.aso]


class _ReportingClient:
    def __init__(self) -> None:
        self.enabled = True
        self.calls: list[dict[str, object]] = []

    def test_result(self, payload: dict[str, object]) -> None:
        self.calls.append(payload)


def test_send_test_result_updates_posts_attempt_two_for_finalized_pms_result(tmp_path) -> None:
    nodeid = "qa/visual/test_demo.py::test_case[a]"
    run_root = tmp_path / "artifacts" / "run-1"
    report_dir = run_root / "visual"
    report_dir.mkdir(parents=True)
    heatmap_rel = "heatmap/case-a.png"
    heatmap_file = report_dir / heatmap_rel
    heatmap_file.parent.mkdir(parents=True, exist_ok=True)
    heatmap_file.write_bytes(b"heat")
    base_payload = {
        "event_type": "test_result",
        "run_uid": "run-uid-1",
        "attempt": 1,
        "test_id": nodeid,
        "nodeid": nodeid,
        "status": "passed",
        "visual": {
            "verdict": "analysis",
            "execution": {"pms_usage_state": "deferred"},
        },
        "artifacts": [
            {"kind": "trace", "path": "trace.zip", "available": True},
        ],
    }
    client = _ReportingClient()
    config = SimpleNamespace(
        _reporting_client=client,
        _test_result_payloads={nodeid: base_payload},
        _run_uid="run-uid-1",
    )
    run_artifacts = SimpleNamespace(run_id="run-1", root=run_root)

    result = VisualResult(
        scenario_id="scenario-1",
        status="passed",
        message="ok",
        compare_mode="hybrid",
        baseline_path="baseline.png",
        actual_path="actual.png",
        diff_path="diff.png",
        heatmap_path=heatmap_rel,
        nodeid=nodeid,
    )
    result.pixel_changed_ratio = 0.001
    result.applied_shift_y = 3
    result.lpips = 0.0
    result.dists = 0.0

    visual_conftest._send_test_result_updates(config, run_artifacts, [result])

    assert len(client.calls) == 1
    payload = cast(dict[str, Any], client.calls[0])
    assert payload["attempt"] == 2
    assert payload["idempotency_key"] == f"test_result:run-uid-1:{nodeid}:2"
    assert payload["visual"]["verdict"] == "passed"
    assert payload["visual"]["scores"]["applied_shift_y"] == 3
    artifacts = cast(list[dict[str, Any]], payload["artifacts"])
    heatmap = next(item for item in artifacts if item.get("kind") == "visual_heatmap")
    assert heatmap["path"] == heatmap_rel
    assert heatmap["available"] is True
    assert heatmap["size_bytes"] == 4
    assert any(item.get("kind") == "trace" for item in artifacts)


def test_send_test_result_updates_marks_missing_heatmap_as_unavailable(tmp_path) -> None:
    nodeid = "qa/visual/test_demo.py::test_case[b]"
    run_root = tmp_path / "artifacts" / "run-2"
    report_dir = run_root / "visual"
    report_dir.mkdir(parents=True)
    heatmap_rel = "heatmap/missing.png"
    base_payload = {
        "event_type": "test_result",
        "run_uid": "run-uid-2",
        "attempt": 1,
        "test_id": nodeid,
        "nodeid": nodeid,
        "status": "passed",
        "visual": {
            "verdict": "analysis",
            "execution": {"pms_usage_state": "deferred"},
        },
    }
    client = _ReportingClient()
    config = SimpleNamespace(
        _reporting_client=client,
        _test_result_payloads={nodeid: base_payload},
        _run_uid="run-uid-2",
    )
    run_artifacts = SimpleNamespace(run_id="run-2", root=run_root)

    result = VisualResult(
        scenario_id="scenario-2",
        status="passed",
        message="ok",
        compare_mode="hybrid",
        baseline_path="baseline.png",
        actual_path="actual.png",
        diff_path="diff.png",
        heatmap_path=heatmap_rel,
        nodeid=nodeid,
    )

    visual_conftest._send_test_result_updates(config, run_artifacts, [result])

    payload = cast(dict[str, Any], client.calls[0])
    artifacts = cast(list[dict[str, Any]], payload["artifacts"])
    heatmap = next(item for item in artifacts if item.get("kind") == "visual_heatmap")
    assert heatmap["path"] == heatmap_rel
    assert heatmap["available"] is False
    assert heatmap["size_bytes"] == 0
    assert heatmap["sha256"] == ""


def test_send_test_result_updates_preserves_failed_dom_artifacts_from_base_payload(tmp_path) -> None:
    """Ensure attempt-2 visual updates preserve unrelated artifacts including failed_dom from base payload."""
    nodeid = "qa/visual/test_demo.py::test_case[failed_with_dom]"
    run_root = tmp_path / "artifacts" / "run-3"
    report_dir = run_root / "visual"
    report_dir.mkdir(parents=True)
    heatmap_rel = "heatmap/case-failed.png"
    heatmap_file = report_dir / heatmap_rel
    heatmap_file.parent.mkdir(parents=True, exist_ok=True)
    heatmap_file.write_bytes(b"heat")

    base_payload = {
        "event_type": "test_result",
        "run_uid": "run-uid-3",
        "attempt": 1,
        "test_id": nodeid,
        "nodeid": nodeid,
        "status": "failed",
        "visual": {
            "verdict": "analysis",
            "execution": {"pms_usage_state": "deferred"},
        },
        "artifacts": [
            {"kind": "trace", "path": "trace.zip", "available": True},
            {"kind": "failed_dom", "path": "failed-dom/case-failed.html", "available": True, "size_bytes": 156},
            {"kind": "screenshot_raw", "path": "screenshots/case-raw.png", "available": True},
        ],
    }
    client = _ReportingClient()
    config = SimpleNamespace(
        _reporting_client=client,
        _test_result_payloads={nodeid: base_payload},
        _run_uid="run-uid-3",
    )
    run_artifacts = SimpleNamespace(run_id="run-3", root=run_root)

    result = VisualResult(
        scenario_id="scenario-3",
        status="failed",
        message="visual comparison failed",
        compare_mode="hybrid",
        baseline_path="baseline.png",
        actual_path="actual.png",
        diff_path="diff.png",
        heatmap_path=heatmap_rel,
        nodeid=nodeid,
    )
    result.pixel_changed_ratio = 0.05
    result.lpips = 0.2
    result.dists = 0.15

    visual_conftest._send_test_result_updates(config, run_artifacts, [result])

    assert len(client.calls) == 1
    payload = cast(dict[str, Any], client.calls[0])
    assert payload["attempt"] == 2
    assert payload["visual"]["verdict"] == "failed"
    artifacts = cast(list[dict[str, Any]], payload["artifacts"])

    # Verify that failed_dom artifact from base payload is preserved
    failed_dom_artifacts = [item for item in artifacts if item.get("kind") == "failed_dom"]
    assert len(failed_dom_artifacts) == 1
    failed_dom = failed_dom_artifacts[0]
    assert failed_dom["path"] == "failed-dom/case-failed.html"
    assert failed_dom["available"] is True
    assert failed_dom["size_bytes"] == 156

    # Verify that other base artifacts are also preserved
    assert any(item.get("kind") == "trace" for item in artifacts)
    assert any(item.get("kind") == "screenshot_raw" for item in artifacts)

    # Verify that visual heatmap is added
    assert any(item.get("kind") == "visual_heatmap" for item in artifacts)
