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


def test_send_test_result_updates_posts_attempt_two_for_finalized_pms_result() -> None:
    nodeid = "qa/visual/test_demo.py::test_case[a]"
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
    }
    client = _ReportingClient()
    config = SimpleNamespace(
        _reporting_client=client,
        _test_result_payloads={nodeid: base_payload},
        _run_uid="run-uid-1",
    )
    run_artifacts = SimpleNamespace(run_id="run-1")

    result = VisualResult(
        scenario_id="scenario-1",
        status="passed",
        message="ok",
        compare_mode="hybrid",
        baseline_path="baseline.png",
        actual_path="actual.png",
        nodeid=nodeid,
    )
    result.pixel_changed_ratio = 0.001
    result.lpips = 0.0
    result.dists = 0.0

    visual_conftest._send_test_result_updates(config, run_artifacts, [result])

    assert len(client.calls) == 1
    payload = cast(dict[str, Any], client.calls[0])
    assert payload["attempt"] == 2
    assert payload["idempotency_key"] == f"test_result:run-uid-1:{nodeid}:2"
    assert payload["visual"]["verdict"] == "passed"
