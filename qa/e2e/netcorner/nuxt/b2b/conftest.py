from dataclasses import replace
import pytest
from framework.env import RuntimeEnv
from framework.url_resolver.url_resolver import url_resolver, EnvUrls

resolve_pl = url_resolver(
    EnvUrls(
        prod="https://bi-to-bi.pl",
        demo="https://sklep-bi-to-bi-demo.komputronik.dev",
        test_template="https://bi-to-bi-{host}.netcorner.pl",
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
        resolved = resolve_pl(env.server_type, env.server_name).rstrip("/")
    except ValueError as e:
        raise pytest.UsageError(f"Cannot resolve base_url for env={env!r}: {e}") from e

    config._runtime_env = replace(env, base_url=resolved)
