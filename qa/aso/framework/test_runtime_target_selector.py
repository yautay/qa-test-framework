from __future__ import annotations

import pytest

from qa.conftest import _normalize_reference_selector, _normalize_target_selector

pytestmark = [pytest.mark.aso]


def test_normalize_target_selector_maps_server_name_alias() -> None:
    server_name, source = _normalize_target_selector("demo")

    assert server_name == "demo"
    assert source == "server_name_alias"


def test_normalize_target_selector_keeps_test_dns_hostname() -> None:
    server_name, source = _normalize_target_selector("testowka.test")

    assert server_name == "testowka.test"
    assert source == "server_name"


def test_normalize_reference_selector_maps_env_alias() -> None:
    reference_host, source = _normalize_reference_selector("prod")

    assert reference_host == "prod"
    assert source == "reference_alias"


def test_normalize_reference_selector_maps_dns_host_to_test_environment() -> None:
    reference_host, source = _normalize_reference_selector("testowka.test")

    assert reference_host == "testowka.test"
    assert source == "reference_host"
