from __future__ import annotations

from typing import Any

from framework.env import RuntimeEnv


def resolve_report_toggles(config: Any, env: RuntimeEnv) -> tuple[bool, bool]:
    cli_allure_enabled = getattr(config.option, "allure_enabled", None)
    cli_pytest_html_enabled = getattr(config.option, "pytest_html_enabled", None)
    allure_enabled = env.allure_enabled if cli_allure_enabled is None else bool(cli_allure_enabled)
    pytest_html_enabled = env.pytest_html_enabled if cli_pytest_html_enabled is None else bool(cli_pytest_html_enabled)
    return allure_enabled, pytest_html_enabled
