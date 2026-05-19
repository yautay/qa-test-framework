from __future__ import annotations

from types import SimpleNamespace

import pytest

from qa.aso import conftest as aso_conftest

pytestmark = [pytest.mark.aso]


class _FakePage:
    def __init__(self) -> None:
        self.default_timeout = None
        self.navigation_timeout = None

    def set_default_timeout(self, value: int) -> None:
        self.default_timeout = value

    def set_default_navigation_timeout(self, value: int) -> None:
        self.navigation_timeout = value


def test_extended_timeout_sets_playwright_timeouts_to_60_seconds() -> None:
    page = _FakePage()

    request = SimpleNamespace(getfixturevalue=lambda name: page)
    aso_conftest.extended_timeout.__wrapped__(request)

    assert page.default_timeout == 60_000
    assert page.navigation_timeout == 60_000


def test_apply_extended_timeout_marker_requests_fixture_when_marker_present() -> None:
    calls: list[str] = []
    node = SimpleNamespace(get_closest_marker=lambda name: object() if name == "aso_extended_timeout" else None)

    def _getfixturevalue(name: str):
        calls.append(name)
        return None

    request = SimpleNamespace(node=node, getfixturevalue=_getfixturevalue)
    aso_conftest._apply_extended_timeout_marker.__wrapped__(request)

    assert calls == ["extended_timeout"]


def test_apply_extended_timeout_marker_skips_when_marker_absent() -> None:
    calls: list[str] = []
    node = SimpleNamespace(get_closest_marker=lambda name: None)

    def _getfixturevalue(name: str):
        calls.append(name)
        return None

    request = SimpleNamespace(node=node, getfixturevalue=_getfixturevalue)
    aso_conftest._apply_extended_timeout_marker.__wrapped__(request)

    assert calls == []
