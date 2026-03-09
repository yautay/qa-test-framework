from dataclasses import replace

import pytest

from framework.env import RuntimeEnv
from qa.visual.netcorner.nuxt.pl.url_config import resolve_runtime_base_url


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return

    if (env.base_url or "").strip():
        return

    # Legacy compatibility: env.server_type + env.server_name split is resolved
    # centrally in qa/conftest.py (including server_name aliases demo/prod/local).
    try:
        resolved = resolve_runtime_base_url(env.server_type, env.server_name)
    except ValueError as e:
        raise pytest.UsageError(f"Cannot resolve base_url for env={env!r}: {e}") from e

    config._runtime_env = replace(env, base_url=resolved)
