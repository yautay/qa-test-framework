from dataclasses import replace
from typing import Any, cast

import pytest

from framework.env import RuntimeEnv
from framework.url_resolver.url_resolver import EnvUrls, url_resolver

resolve_pl = url_resolver(
    EnvUrls(
        prod="https://bi-to-bi.pl",
        demo="https://sklep-bi-to-bi-demo.komputronik.dev",
        test_template="https://bi-to-bi-{host}.netcorner.pl",
        local="https://bi-to-bi.local",
    )
)


@pytest.fixture(scope="session")
def runtime_env(pytestconfig: pytest.Config) -> RuntimeEnv:
    env: RuntimeEnv = cast(Any, pytestconfig)._runtime_env
    if (env.base_url or "").strip():
        return env

    try:
        resolved = resolve_pl(env.server_name).rstrip("/")
    except ValueError as e:
        raise pytest.UsageError(f"Cannot resolve base_url for env={env!r}: {e}") from e

    return replace(env, base_url=resolved)
