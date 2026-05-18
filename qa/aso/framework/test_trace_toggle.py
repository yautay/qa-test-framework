from __future__ import annotations

import pytest

from framework.env import load_env

pytestmark = [pytest.mark.aso]


def test_trace_enabled_defaults_to_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRACE_ENABLED", raising=False)
    env = load_env()
    assert env.trace_enabled is True


def test_trace_enabled_respects_env_var_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRACE_ENABLED", "0")
    env = load_env()
    assert env.trace_enabled is False


def test_trace_enabled_respects_env_var_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRACE_ENABLED", "1")
    env = load_env()
    assert env.trace_enabled is True
