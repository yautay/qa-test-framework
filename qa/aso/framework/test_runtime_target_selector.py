from __future__ import annotations

import pytest

from qa.conftest import _normalize_reference_selector, _normalize_target_selector

pytestmark = [pytest.mark.aso]


def test_normalize_target_selector_maps_server_name_alias_to_legacy_server_type() -> None:
    server_type, server_name, source = _normalize_target_selector("test", "demo")

    assert server_type == "demo"
    assert server_name == ""
    assert source == "server_name_alias"


def test_normalize_target_selector_keeps_test_dns_hostname() -> None:
    server_type, server_name, source = _normalize_target_selector("test", "testowka.test")

    assert server_type == "test"
    assert server_name == "testowka.test"
    assert source == "legacy_server_type"


def test_normalize_reference_selector_maps_env_alias() -> None:
    server_type, server_name, source = _normalize_reference_selector("prod")

    assert server_type == "prod"
    assert server_name == ""
    assert source == "reference_alias"


def test_normalize_reference_selector_maps_dns_host_to_test_environment() -> None:
    server_type, server_name, source = _normalize_reference_selector("testowka.test")

    assert server_type == "test"
    assert server_name == "testowka.test"
    assert source == "reference_host"
