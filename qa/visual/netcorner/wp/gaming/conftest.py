from dataclasses import replace

import pytest

from framework.env import RuntimeEnv
from framework.url_resolver.url_resolver import EnvUrls, url_resolver

resolve_gaming = url_resolver(
    EnvUrls(
        prod="https://gaming.komputronik.pl/",
        demo="https://gaming-demo.ktr.pl",
        test_template="https://wp-komputronik-gaming{host}.netcorner.pl",
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
        resolved = resolve_gaming(env.server_name).rstrip("/")
    except ValueError as e:
        raise pytest.UsageError(f"Cannot resolve base_url for env={env!r}: {e}") from e

    config._runtime_env = replace(env, base_url=resolved)
