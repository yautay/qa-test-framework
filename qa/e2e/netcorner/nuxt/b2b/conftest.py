from __future__ import annotations

from dataclasses import replace

from framework.env import RuntimeEnv


def _resolve_b2b_nuxt_base_url(server_type: str, server_name: str) -> str:
    env_type = server_type.strip().lower()

    if env_type == "test":
        return f"https://komputronik-{server_name}.netcorner.pl"
    if env_type == "demo":
        return "https://sklep3-demo.komputronik.dev"
    if env_type == "prod":
        return "https://komputronik.pl"
    if env_type == "local":
        return "https://komputronik.local"
    return ""


def pytest_configure(config) -> None:
    runtime_env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if runtime_env is None or runtime_env.base_url:
        return

    resolved_base_url = _resolve_b2b_nuxt_base_url(runtime_env.server_type, runtime_env.server_name)
    config._runtime_env = replace(runtime_env, base_url=resolved_base_url)
