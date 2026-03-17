from __future__ import annotations

import pytest

import settings
from framework.env import load_env

pytestmark = [pytest.mark.aso]


def test_load_env_reads_browser_from_environment(monkeypatch):
    monkeypatch.setenv("BROWSER", "chrome")

    env = load_env()

    assert env.browser == "chrome"


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


def test_load_env_reads_allure_toggle_from_environment(monkeypatch):
    monkeypatch.setenv("ALLURE_ENABLED", "1")

    env = load_env()

    assert env.allure_enabled is True


def test_load_env_reads_pytest_html_toggle_from_environment(monkeypatch):
    monkeypatch.setenv("PYTEST_HTML_ENABLED", "0")

    env = load_env()

    assert env.pytest_html_enabled is False


def test_load_env_uses_settings_defaults_for_report_toggles(monkeypatch):
    monkeypatch.delenv("ALLURE_ENABLED", raising=False)
    monkeypatch.delenv("PYTEST_HTML_ENABLED", raising=False)

    env = load_env()

    assert env.allure_enabled is bool(settings.allure_enabled)
    assert env.pytest_html_enabled is bool(settings.pytest_html_enabled)


def test_load_env_reads_visual_freeze_animations_from_environment(monkeypatch):
    monkeypatch.setenv("VISUAL_FREEZE_ANIMATIONS", "0")

    env = load_env()

    assert env.visual_freeze_animations is False


def test_load_env_reads_visual_shift_compensation_from_environment(monkeypatch):
    monkeypatch.setenv("VISUAL_SHIFT_COMPENSATION_Y_PX", "7")

    env = load_env()

    assert env.visual_shift_compensation_y_px == 7
