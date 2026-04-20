from __future__ import annotations

from typing import Any, cast

import pytest

from framework.base.page_objects.base_component import BaseComponent

pytestmark = [pytest.mark.aso]


class _FakeLocatorItem:
    def __init__(self, *, visible: bool, name: str) -> None:
        self._visible = visible
        self.name = name
        self.click_calls = 0
        self.fill_calls: list[str] = []
        self.type_calls: list[str] = []
        self.scroll_calls = 0

    @property
    def first(self) -> _FakeLocatorItem:
        return self

    def count(self) -> int:
        return 1

    def nth(self, _index: int) -> _FakeLocatorItem:
        return self

    def is_visible(self) -> bool:
        return self._visible

    def scroll_into_view_if_needed(self) -> None:
        self.scroll_calls += 1

    def click(self, *, timeout: int) -> None:
        _ = timeout
        self.click_calls += 1

    def fill(self, value: str, *, timeout: int) -> None:
        _ = timeout
        self.fill_calls.append(value)

    def type(self, value: str, *, timeout: int) -> None:
        _ = timeout
        self.type_calls.append(value)


class _FakeLocatorGroup:
    def __init__(self, items: list[_FakeLocatorItem]) -> None:
        self._items = items

    @property
    def first(self) -> _FakeLocatorItem:
        return self._items[0]

    def count(self) -> int:
        return len(self._items)

    def nth(self, index: int) -> _FakeLocatorItem:
        return self._items[index]


class _FakeExpectation:
    def __init__(self, locator: Any) -> None:
        self.locator = locator

    def to_be_visible(self, *, timeout: int) -> None:
        _ = timeout

    def to_be_enabled(self, *, timeout: int) -> None:
        _ = timeout


def test_first_visible_prefers_first_visible_match() -> None:
    hidden = _FakeLocatorItem(visible=False, name="hidden")
    visible = _FakeLocatorItem(visible=True, name="visible")
    locator = _FakeLocatorGroup([hidden, visible])

    selected = BaseComponent.first_visible(cast(Any, locator))

    assert selected is visible


def test_first_visible_falls_back_to_first_when_no_visible() -> None:
    first = _FakeLocatorItem(visible=False, name="first")
    second = _FakeLocatorItem(visible=False, name="second")
    locator = _FakeLocatorGroup([first, second])

    selected = BaseComponent.first_visible(cast(Any, locator))

    assert selected is first


def test_safe_click_uses_visible_match(monkeypatch: pytest.MonkeyPatch) -> None:
    hidden = _FakeLocatorItem(visible=False, name="hidden")
    visible = _FakeLocatorItem(visible=True, name="visible")
    locator = _FakeLocatorGroup([hidden, visible])
    component = BaseComponent(cast(Any, locator))

    monkeypatch.setattr(
        "framework.base.page_objects.base_component.expect",
        lambda target: _FakeExpectation(target),
    )

    component.safe_click(cast(Any, locator))

    assert hidden.click_calls == 0
    assert visible.click_calls == 1
    assert visible.scroll_calls == 1
