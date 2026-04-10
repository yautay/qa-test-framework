from __future__ import annotations

from pathlib import Path

import pytest

import framework.logger as logger_module
from framework.logger import _allow_console_record

pytestmark = [pytest.mark.aso]


def _record(name: str, message: str) -> dict[str, str]:
    return {
        "name": name,
        "message": message,
    }


def test_allow_console_record_hides_reporting_transport_logs_when_enabled() -> None:
    assert (
        _allow_console_record(
            _record("framework.reporting.http_sender", "reporting_api_non_2xx"),
            suppress_reporting_api_logs=True,
        )
        is False
    )
    assert (
        _allow_console_record(
            _record("framework.reporting.async_queue", "reporting_async_http_send_start"),
            suppress_reporting_api_logs=True,
        )
        is False
    )


def test_allow_console_record_keeps_non_reporting_logs_when_enabled() -> None:
    assert (
        _allow_console_record(
            _record("qa.conftest", "reporting_run_start"),
            suppress_reporting_api_logs=True,
        )
        is True
    )
    assert (
        _allow_console_record(
            _record("framework.reporting_client", "reporting_client_initialized"),
            suppress_reporting_api_logs=True,
        )
        is True
    )


def test_allow_console_record_can_disable_suppression() -> None:
    assert (
        _allow_console_record(
            _record("framework.reporting.http_sender", "reporting_api_call_failed"),
            suppress_reporting_api_logs=False,
        )
        is True
    )


@pytest.mark.parametrize(
    ("suppress_env", "expected"),
    [
        ("1", False),
        ("0", True),
    ],
)
def test_configure_tools_logging_applies_reporting_filter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    suppress_env: str,
    expected: bool,
) -> None:
    class _LoggerStub:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

        def remove(self, *args: object, **kwargs: object) -> None:
            self.calls.append(("remove", args, kwargs))

        def configure(self, *args: object, **kwargs: object) -> None:
            self.calls.append(("configure", args, kwargs))

        def add(self, *args: object, **kwargs: object) -> int:
            self.calls.append(("add", args, kwargs))
            return 1

    stub = _LoggerStub()
    monkeypatch.setenv("CONSOLE_SUPPRESS_REPORTING_API_LOGS", suppress_env)
    monkeypatch.setattr(logger_module, "logger", stub)
    monkeypatch.setattr(logger_module, "_install_stdlib_logging_bridge", lambda: None)

    expected_log_path = tmp_path / "tools.log"
    monkeypatch.setattr(logger_module, "add_tools_file_sink", lambda _script_name: expected_log_path)

    result = logger_module.configure_tools_logging("tools_test")

    assert result == expected_log_path
    add_calls = [call for call in stub.calls if call[0] == "add"]
    assert add_calls
    console_add_kwargs = add_calls[0][2]
    filter_fn = console_add_kwargs.get("filter")
    assert callable(filter_fn)
    assert (
        filter_fn({"name": "framework.reporting.http_sender", "message": "reporting_api_non_2xx"})  # type: ignore[misc]
        is expected
    )
