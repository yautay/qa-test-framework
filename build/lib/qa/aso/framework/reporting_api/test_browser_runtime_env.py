from __future__ import annotations

import pytest

from framework.env import load_env

pytestmark = [pytest.mark.aso]


def test_load_env_reads_browser_from_environment(monkeypatch):
    monkeypatch.setenv("BROWSER", "chrome")

    env = load_env()

    assert env.browser == "chrome"
    assert env.headless is True


def test_load_env_uses_settings_browser_by_default(monkeypatch):
    monkeypatch.delenv("BROWSER", raising=False)

    env = load_env()

    assert env.browser == "chromium"


def test_load_env_reads_grid_runtime_from_environment(monkeypatch):
    monkeypatch.setenv("IS_GRID_AVAILABLE", "1")
    monkeypatch.setenv("GRID_WS_ENDPOINT", "ws://127.0.0.1:9323/")
    monkeypatch.setenv("GRID_CONNECT_TIMEOUT_MS", "45000")

    env = load_env()

    assert env.is_grid_available is True
    assert env.grid_ws_endpoint == "ws://127.0.0.1:9323/"
    assert env.grid_connect_timeout_ms == 45000


def test_load_env_reads_reference_host_from_environment(monkeypatch):
    monkeypatch.setenv("REFERENCE_HOST", "demo")

    env = load_env()

    assert env.reference_host == "demo"
