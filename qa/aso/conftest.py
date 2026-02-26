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


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    aso_root = Path(__file__).resolve().parent
    for item in items:
        try:
            item_path = Path(str(item.fspath)).resolve()
        except Exception:
            continue
        if aso_root in item_path.parents or item_path == aso_root:
            item.add_marker(pytest.mark.aso)
