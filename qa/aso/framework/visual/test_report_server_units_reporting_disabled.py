from __future__ import annotations

from typing import Any

import pytest

from framework.reporting.report_server.state import _treat_reporting_disabled_as_success

pytestmark = [pytest.mark.aso]


def test_treat_reporting_disabled_as_success_updates_only_reporting_events() -> None:
    state: dict[str, Any] = {
        "test_cases": {
            "case-1": {
                "bug": {"locked": True, "synced": False, "note": ""},
                "aso": {"locked": True, "synced": False, "note": ""},
            },
            "case-2": {
                "bug": {"locked": False, "synced": False, "note": ""},
                "aso": {"locked": False, "synced": False, "note": ""},
            },
        },
        "outbox": [
            {"event_id": "b1", "type": "BUG_SET", "status": "pending", "test_case_id": "case-1"},
            {"event_id": "a1", "type": "ASO_SET", "status": "failed", "test_case_id": "case-1"},
            {"event_id": "n1", "type": "NOTE_UPSERT", "status": "failed", "test_case_id": "case-1"},
            {"event_id": "b2", "type": "BUG_SET", "status": "sent", "test_case_id": "case-1"},
            {"event_id": "a2", "type": "ASO_SET", "status": "superseded", "test_case_id": "case-1"},
        ],
    }

    synced_cases, sent_events = _treat_reporting_disabled_as_success(state)

    assert synced_cases == 1
    assert sent_events == 2
    assert state["test_cases"]["case-1"]["bug"]["synced"] is True
    assert state["test_cases"]["case-1"]["aso"]["synced"] is True
    assert state["test_cases"]["case-2"]["bug"]["synced"] is False
    assert state["outbox"][0]["status"] == "sent"
    assert state["outbox"][1]["status"] == "sent"
    assert state["outbox"][2]["status"] == "failed"
    assert state["outbox"][3]["status"] == "sent"
    assert state["outbox"][4]["status"] == "superseded"
