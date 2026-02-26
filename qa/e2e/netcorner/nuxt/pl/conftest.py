from dataclasses import replace
from pathlib import Path

import pytest
from playwright.sync_api import Browser

from framework.env import RuntimeEnv
from framework.url_resolver.url_resolver import url_resolver, EnvUrls
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.cookie_notice import CookieNotice

resolve_pl = url_resolver(
    EnvUrls(
        prod="https://komputronik.pl",
        demo="https://sklep3-demo.komputronik.dev",
        test_template="https://komputronik-{host}.netcorner.pl",
    )
)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    markexpr = str(getattr(config.option, "markexpr", "") or "").strip().lower()
    if markexpr == "visual":
        return

    env: RuntimeEnv | None = getattr(config, "_runtime_env", None)
    if env is None:
        return

    if (env.base_url or "").strip():
        return

    # Legacy compatibility: env.server_type + env.server_name split is resolved
    # centrally in qa/conftest.py (including server_name aliases demo/prod/local).
    try:
        resolved = resolve_pl(env.server_type, env.server_name).rstrip("/")
    except ValueError as e:
        raise pytest.UsageError(f"Cannot resolve base_url for env={env!r}: {e}") from e

    config._runtime_env = replace(env, base_url=resolved)


@pytest.fixture(scope="session")
def storage_state(browser: Browser, runtime_env: RuntimeEnv, tmp_path_factory: pytest.TempPathFactory) -> str | None:
    base_url = (runtime_env.base_url or "").strip()
    if not base_url:
        return None

    state_dir = tmp_path_factory.mktemp("netcorner_pl_state")
    state_path = Path(state_dir) / "storage_state.json"

    context = browser.new_context(ignore_https_errors=runtime_env.ignore_https_errors)
    page = context.new_page()
    page.goto(base_url, wait_until="domcontentloaded", timeout=10_000)
    CookieNotice(page).dismiss_if_present()
    context.storage_state(path=str(state_path))
    context.close()
    return str(state_path)
