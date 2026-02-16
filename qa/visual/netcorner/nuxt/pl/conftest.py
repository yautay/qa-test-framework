from dataclasses import replace
import pytest
from framework.env import RuntimeEnv
from qa.auxiliary.url_netcorner_pl import resolve_pl_nuxt_base_url


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return

    if (env.base_url or "").strip():
        return

    resolved = resolve_pl_nuxt_base_url(env.server_type, env.server_name)
    if not resolved:
        pytest.exit(
            "base_url is empty. Provide --base-url or valid --server-type/--server-name",
            returncode=2,
        )

    config._runtime_env = replace(env, base_url=resolved)