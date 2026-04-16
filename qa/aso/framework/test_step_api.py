from __future__ import annotations

import pytest

from qa.e2e.netcorner.lib import step_api

pytestmark = [pytest.mark.aso]


def test_step_decorator_records_formatted_title() -> None:
    token = step_api.start_test_step_trace("qa/e2e/sample.py::test_case")
    try:

        @step_api.step("Wpisuję wartość: {value}")
        def _run(value: str) -> str:
            return value.upper()

        assert _run("abc") == "ABC"
    finally:
        step_api.stop_test_step_trace(token)

    payload = step_api.pop_test_step_trace("qa/e2e/sample.py::test_case")
    assert len(payload) == 1
    assert payload[0]["title"] == "Wpisuję wartość: abc"
    assert payload[0]["status"] == "passed"
    assert int(payload[0]["duration_ms"]) >= 0


def test_step_context_records_failure_with_error_message() -> None:
    token = step_api.start_test_step_trace("qa/e2e/sample.py::test_failing_case")
    try:
        with pytest.raises(RuntimeError, match="boom"):
            with step_api.step_context("Krok kończy się błędem"):
                raise RuntimeError("boom")
    finally:
        step_api.stop_test_step_trace(token)

    payload = step_api.pop_test_step_trace("qa/e2e/sample.py::test_failing_case")
    assert len(payload) == 1
    assert payload[0]["status"] == "failed"
    assert payload[0]["title"] == "Krok kończy się błędem"
    assert "boom" in str(payload[0].get("error", ""))
