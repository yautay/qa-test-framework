from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from framework.env import RuntimeEnv, load_env
from qa.e2e.netcorner.nuxt.b2b import conftest as b2b_conftest
from qa.e2e.netcorner.nuxt.pl import conftest as pl_conftest

pytestmark = [pytest.mark.aso]


def _config_with_env(env: RuntimeEnv) -> SimpleNamespace:
    return SimpleNamespace(_runtime_env=env)


def test_pl_runtime_env_fixture_resolves_pl_base_url_without_global_mutation() -> None:
    source_env = replace(load_env(), base_url="", server_type="test", server_name="weryfikacja.alfa")
    config = _config_with_env(source_env)

    resolved_env = pl_conftest.runtime_env.__wrapped__(config)

    assert resolved_env.base_url == "https://komputronik-weryfikacja.alfa.netcorner.pl"
    assert config._runtime_env.base_url == ""


def test_b2b_runtime_env_fixture_resolves_b2b_base_url_without_global_mutation() -> None:
    source_env = replace(load_env(), base_url="", server_type="test", server_name="weryfikacja.alfa")
    config = _config_with_env(source_env)

    resolved_env = b2b_conftest.runtime_env.__wrapped__(config)

    assert resolved_env.base_url == "https://bi-to-bi-weryfikacja.alfa.netcorner.pl"
    assert config._runtime_env.base_url == ""


@pytest.mark.parametrize(
    ("fixture_func", "existing_base_url"),
    [
        (pl_conftest.runtime_env.__wrapped__, "https://komputronik.pl"),
        (b2b_conftest.runtime_env.__wrapped__, "https://bi-to-bi.pl"),
    ],
)
def test_suite_runtime_env_fixtures_preserve_explicit_base_url(
    fixture_func,
    existing_base_url: str,
) -> None:
    source_env = replace(load_env(), base_url=existing_base_url, server_type="test", server_name="weryfikacja.alfa")
    config = _config_with_env(source_env)

    resolved_env = fixture_func(config)

    assert resolved_env.base_url == existing_base_url
    assert resolved_env is source_env
