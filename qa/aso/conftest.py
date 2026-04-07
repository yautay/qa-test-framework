from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def aso(runtime_env) -> dict[str, str | bool]:
    """ASO suite context fixture for technical/framework tests."""
    return {
        "suite": "aso",
        "browser": runtime_env.browser,
        "headless": runtime_env.headless,
    }


@pytest.fixture(autouse=True)
def _aso_autouse(aso) -> None:
    _ = aso


@pytest.fixture(scope="function", autouse=True)
def _apply_extended_timeout_marker(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("extended_timeout") is None:
        return
    request.getfixturevalue("extended_timeout")


@pytest.fixture(scope="function")
def extended_timeout(request: pytest.FixtureRequest) -> None:
    try:
        page = request.getfixturevalue("page")
    except pytest.FixtureLookupError:
        return
    page.set_default_timeout(60_000)
    page.set_default_navigation_timeout(60_000)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    aso_root = Path(__file__).resolve().parent
    for item in items:
        try:
            item_path = Path(str(item.fspath)).resolve()
        except Exception:
            continue
        if aso_root in item_path.parents or item_path == aso_root:
            item.add_marker(pytest.mark.aso)
