from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from qa.conftest import _assert_supported_plugin_profile

pytestmark = [pytest.mark.aso]


def _config_with_plugins(*entries: tuple[str, str | None], blocked: tuple[str, ...] = ()) -> SimpleNamespace:
    plugins = []
    for name, module_name in entries:
        plugin = None if module_name is None else SimpleNamespace(__name__=module_name)
        plugins.append((name, plugin))
    blocked_set = {item for item in blocked}
    pluginmanager = SimpleNamespace(
        list_name_plugin=lambda: plugins,
        is_blocked=lambda name: str(name or "") in blocked_set,
    )
    return SimpleNamespace(pluginmanager=pluginmanager)


def test_plugin_profile_guard_accepts_supported_plugins() -> None:
    config = _config_with_plugins(
        ("xdist", "xdist.plugin"),
        ("allure_pytest", "allure_pytest.plugin"),
        ("pytest_html", "pytest_html.plugin"),
    )

    _assert_supported_plugin_profile(cast(Any, config))


@pytest.mark.parametrize(
    "plugin_name,module_name",
    [
        ("anyio", "anyio.pytest_plugin"),
        ("playwright", "pytest_playwright.pytest_playwright"),
        ("pytest_playwright", "pytest_playwright.pytest_playwright"),
        ("base_url", "pytest_base_url.plugin"),
        ("pytest_base_url", "pytest_base_url.plugin"),
    ],
)
def test_plugin_profile_guard_rejects_conflicting_plugins(plugin_name: str, module_name: str) -> None:
    config = _config_with_plugins((plugin_name, module_name))

    with pytest.raises(pytest.UsageError, match="Unsupported pytest plugin profile"):
        _assert_supported_plugin_profile(cast(Any, config))


def test_plugin_profile_guard_ignores_blocked_or_none_plugins() -> None:
    config = _config_with_plugins(
        ("anyio", None),
        ("pytest_playwright", None),
        ("pytest_base_url", None),
        blocked=("anyio", "pytest_playwright", "pytest_base_url"),
    )

    _assert_supported_plugin_profile(cast(Any, config))
