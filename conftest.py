from __future__ import annotations
import pytest
import settings


def pytest_addoption(parser: pytest.Parser) -> None:
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

    --server-type
        Target environment type.
        Typical values:
            - test
            - demo
            - prod
            - local

        Example:
            pytest --server-type=test

    --server-name
        Optional server identifier within the environment.

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
        "--server-type",
        action="store",
        default=None,
        choices=("test", "demo", "prod", "local"),
        help="Target environment type",
    )
    parser.addoption(
        "--server-name",
        action="store",
        default=None,
        help="Server name for test env",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Override resolved base url",
    )
