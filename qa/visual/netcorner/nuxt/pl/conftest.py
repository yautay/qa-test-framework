from dataclasses import replace

import pytest

from framework.env import RuntimeEnv
from framework.url_resolver.url_resolver import EnvUrls, url_resolver

resolve_pl = url_resolver(
    EnvUrls(
        prod="https://komputronik.pl",
        demo="https://sklep3-demo.komputronik.dev",
        test_template="https://komputronik-{host}.netcorner.pl",
        local="https://komputronik.local",
    )
)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return

    if (env.base_url or "").strip():
        return

    try:
        resolved = resolve_pl(env.server_name).rstrip("/")
    except ValueError as e:
        raise pytest.UsageError(f"Cannot resolve base_url for env={env!r}: {e}") from e

    config._runtime_env = replace(env, base_url=resolved)
