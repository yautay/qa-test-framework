from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from framework.env import load_env
from framework.reporting.toggles import resolve_report_toggles
from qa.e2e import conftest as e2e_conftest

pytestmark = [pytest.mark.aso]


def _config_with_cli(*, allure_enabled, pytest_html_enabled) -> SimpleNamespace:
    return SimpleNamespace(
        option=SimpleNamespace(
            allure_enabled=allure_enabled,
            pytest_html_enabled=pytest_html_enabled,
        )
    )


def test_report_toggle_resolver_prefers_runtime_env_when_cli_not_set() -> None:
    env = replace(load_env(), allure_enabled=False, pytest_html_enabled=True)
    config = _config_with_cli(allure_enabled=None, pytest_html_enabled=None)

    allure_enabled, pytest_html_enabled = resolve_report_toggles(config, env)

    assert allure_enabled is False
    assert pytest_html_enabled is True

    allure_enabled, pytest_html_enabled = e2e_conftest._resolve_report_toggles(config, env)

    assert allure_enabled is False
    assert pytest_html_enabled is True


def test_report_toggle_resolver_prefers_cli_over_runtime_env() -> None:
    env = replace(load_env(), allure_enabled=False, pytest_html_enabled=True)
    config = _config_with_cli(allure_enabled=True, pytest_html_enabled=False)

    allure_enabled, pytest_html_enabled = resolve_report_toggles(config, env)

    assert allure_enabled is True
    assert pytest_html_enabled is False

    allure_enabled, pytest_html_enabled = e2e_conftest._resolve_report_toggles(config, env)

    assert allure_enabled is True
    assert pytest_html_enabled is False
