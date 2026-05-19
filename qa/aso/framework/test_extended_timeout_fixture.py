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

