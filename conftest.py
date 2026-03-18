from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, cast

import pytest
import settings

from framework.artifacts import resolve_artifacts_base_dir
from framework.env import RuntimeEnv, load_env


pytest_plugins = ("framework.plugins.xdist_report_finalize",)


def _looks_like_e2e_selection(config: pytest.Config) -> bool:
    root = Path(str(config.rootpath)).resolve()
    qa_root = (root / "qa").resolve()
    e2e_root = (qa_root / "e2e").resolve()

    raw_args = cast(tuple[Any, ...], tuple(getattr(config, "args", ()) or ()))
    if not raw_args:
        return True

    for raw in raw_args:
        token = str(raw or "").strip().replace("\\", "/")
        if not token:
            continue
        token_path = token.split("::", 1)[0]
        candidate = Path(token_path)
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()
        else:
            candidate = candidate.resolve()

        if candidate == root or candidate == qa_root:
            return True
        if e2e_root == candidate or e2e_root in candidate.parents:
            return True

    return False


def _resolve_report_run_id(config: pytest.Config) -> str:
    worker_input = cast(Any, getattr(config, "workerinput", None))
    if isinstance(worker_input, dict):
        worker_run_id = str(worker_input.get("run_id") or "").strip()
        if worker_run_id:
            return worker_run_id

    shared_run_id = str(getattr(config, "_shared_run_id", "") or "").strip()
    if shared_run_id:
        return shared_run_id

    env_run_id = str(os.getenv("PYTEST_XDIST_TESTRUNUID") or "").strip()
    if env_run_id:
        return env_run_id

    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def _resolve_report_toggles(config: pytest.Config, env: RuntimeEnv) -> tuple[bool, bool]:
    cli_allure_enabled = getattr(config.option, "allure_enabled", None)
    cli_pytest_html_enabled = getattr(config.option, "pytest_html_enabled", None)
    allure_enabled = env.allure_enabled if cli_allure_enabled is None else bool(cli_allure_enabled)
    pytest_html_enabled = env.pytest_html_enabled if cli_pytest_html_enabled is None else bool(cli_pytest_html_enabled)
    return allure_enabled, pytest_html_enabled


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    if not _looks_like_e2e_selection(config):
        return

    run_id = _resolve_report_run_id(config)
    cast(Any, config)._shared_run_id = run_id
    os.environ.setdefault("PYTEST_XDIST_TESTRUNUID", run_id)

    env = load_env()
    allure_enabled, pytest_html_enabled = _resolve_report_toggles(config, env)
    cast(Any, config)._allure_enabled = allure_enabled
    cast(Any, config)._pytest_html_enabled = pytest_html_enabled

    artifacts_base = resolve_artifacts_base_dir(env.artifacts_dir, config.rootpath)
    run_root = (artifacts_base / run_id).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    current_allure_dir = str(getattr(config.option, "allure_report_dir", "") or "").strip()
    if hasattr(config.option, "allure_report_dir") and allure_enabled and not current_allure_dir:
        allure_results_dir = run_root / "allure-results"
        allure_results_dir.mkdir(parents=True, exist_ok=True)
        cast(Any, config.option).allure_report_dir = str(allure_results_dir)
    if hasattr(config.option, "allure_report_dir") and not allure_enabled:
        cast(Any, config.option).allure_report_dir = ""

    current_html_path = str(getattr(config.option, "htmlpath", "") or "").strip()
    if hasattr(config.option, "htmlpath") and pytest_html_enabled and not current_html_path:
        cast(Any, config.option).htmlpath = str(run_root / "pytest-report.html")
        cast(Any, config.option).self_contained_html = True
    if hasattr(config.option, "htmlpath") and not pytest_html_enabled:
        cast(Any, config.option).htmlpath = ""


def _validate_run_note(value: str) -> str:
    text = str(value or "").strip()
    if len(text) > 50:
        raise pytest.UsageError("--run_note accepts at most 50 characters")
    return text


def pytest_addoption(parser: pytest.Parser) -> None:
    def _has_option(option_name: str) -> bool:
        return option_name in getattr(parser, "_option_string_actions", {})

    """
    Register custom command-line options for pytest.

    These options allow controlling test execution context,
    visual regression behavior, and target environments
    directly from the CLI.

    Available options
    -----------------

    --viewport
        Browser viewport preset used by tests.
        Allowed values:
            - mobile
            - tablet
            - fhd (default)
            - 2k
            - 4k

        Example:
            pytest --viewport=mobile

    --visual-approve
        If provided, current visual screenshots are approved
        and saved as new baselines.

        Default: False

        Example:
            pytest --visual-approve

    --visual-scenario
        Runs only visual scenarios whose name contains
        the provided substring.

        Example:
            pytest --visual-scenario=checkout

    --visual-viewports
        Comma-separated list of viewport presets used for
        visual testing runs.

        Example:
            pytest --visual-viewports=mobile,tablet,fhd

    --server-name
        Target selector for environment routing.
        Values:
            - demo / prod / local
            - DNS hostname token (e.g. weryfikacja.alfa)

        Example:
            pytest --server-name=qa01

    --base-url
        Explicit base URL override. If provided, it should
        take precedence over URLs resolved from environment
        settings.

        Example:
            pytest --base-url=https://example.test

    Notes
    -----
    - These options only register CLI parameters.
    - Actual behavior must be implemented in fixtures or helpers
      using:

          request.config.getoption("<option_name>")

    - Typical usage pattern:

          value = request.config.getoption("--viewport")
    """

    parser.addoption(
        "--viewport",
        action="store",
        default="fhd",
        choices=tuple(settings.visual_viewport_presets.keys()),
        help="Viewport preset for browser context",
    )
    parser.addoption(
        "--server-name",
        action="store",
        default=None,
        help="Target selector (demo/prod/local or DNS hostname)",
    )
    parser.addoption(
        "--reference-host",
        action="store",
        default=None,
        help="Visual dual-pass reference selector (demo/prod/local or test DNS host)",
    )
    if not _has_option("--base-url"):
        try:
            parser.addoption(
                "--base-url",
                action="store",
                default=None,
                help="Override resolved base url",
            )
        except ValueError as exc:
            if "--base-url" not in str(exc):
                raise
    parser.addoption(
        "--tester",
        action="store",
        default=None,
        help="Tester name attached to run/test metadata",
    )
    parser.addoption(
        "--run_note",
        action="store",
        default=None,
        type=_validate_run_note,
        help="Optional run note (max 50 chars) attached to run/test metadata",
    )
    parser.addoption(
        "--allure-enabled",
        action="store_true",
        dest="allure_enabled",
        default=None,
        help="Enable automatic Allure results directory setup",
    )
    parser.addoption(
        "--allure-disabled",
        action="store_false",
        dest="allure_enabled",
        help="Disable automatic Allure results directory setup",
    )
    parser.addoption(
        "--pytest-html-enabled",
        action="store_true",
        dest="pytest_html_enabled",
        default=None,
        help="Enable automatic pytest-html report path setup",
    )
    parser.addoption(
        "--pytest-html-disabled",
        action="store_false",
        dest="pytest_html_enabled",
        help="Disable automatic pytest-html report path setup",
    )


@pytest.fixture(scope="function", autouse=True)
def _apply_extended_timeout_marker(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("extended_timeout") is None:
        return
    request.getfixturevalue("extended_timeout")


@pytest.fixture(scope="function")
def extended_timeout(request: pytest.FixtureRequest) -> None:
    """Extend Playwright default action/navigation timeout for marked tests."""
    try:
        page = request.getfixturevalue("page")
    except pytest.FixtureLookupError:
        return
    page.set_default_timeout(60_000)
    page.set_default_navigation_timeout(60_000)
