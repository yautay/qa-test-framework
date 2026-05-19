from dataclasses import replace
from typing import Any, cast

import pytest

from framework.env import RuntimeEnv
from framework.targeting import resolve_base_url


@pytest.fixture(scope="session")
def runtime_env(pytestconfig: pytest.Config) -> RuntimeEnv:
    env: RuntimeEnv = cast(Any, pytestconfig)._runtime_env
    if (env.base_url or "").strip():
        return env

    try:
        resolved = resolve_base_url(target_id="netcorner-nuxt-pl", server_name=env.server_name)
    except ValueError as e:
        raise pytest.UsageError(f"Cannot resolve base_url for env={env!r}: {e}") from e

    return replace(env, base_url=resolved)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    from pathlib import Path

    suite_root = Path(__file__).parent.resolve()
    for item in items:
        try:
            item_path = Path(item.fspath).resolve()
        except Exception:
            continue
        if suite_root in item_path.parents:
            item.add_marker(pytest.mark.e2e_pl)
