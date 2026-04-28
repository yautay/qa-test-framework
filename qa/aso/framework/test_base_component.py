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
        self.evaluate_calls = 0
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

    def locator(self, selector: str) -> _FakeLocatorItem:
        """Support chained .locator(':visible').first pattern."""
        return self

    def scroll_into_view_if_needed(self) -> None:
        self.scroll_calls += 1

    def click(self, *, timeout: int) -> None:
        _ = timeout
        self.click_calls += 1

    def evaluate(self, script: str) -> None:
        _ = script
        self.evaluate_calls += 1

    def fill(self, value: str, *, timeout: int) -> None:
        _ = timeout
        self.fill_calls.append(value)

    def type(self, value: str, *, timeout: int) -> None:
        _ = timeout
        self.type_calls.append(value)


class _FakeLocatorGroup:
    def __init__(self, items: list[_FakeLocatorItem]) -> None:
        self._items = items
        self._visible_items = [i for i in items if i._visible]

    @property
    def first(self) -> _FakeLocatorItem:
        return self._items[0]

    def count(self) -> int:
        return len(self._items)

    def nth(self, index: int) -> _FakeLocatorItem:
        return self._items[index]

    def locator(self, selector: str) -> _FakeLocatorGroup:
        """Simulate :visible filtering."""
        if ":visible" in selector:
            return _FakeLocatorGroup(self._visible_items if self._visible_items else self._items)
        return self


class _FakeExpectation:
    def __init__(self, locator: Any) -> None:
        self.locator = locator

    def to_be_visible(self, *, timeout: int) -> None:
        _ = timeout

    def to_be_enabled(self, *, timeout: int) -> None:
        _ = timeout


def test_pick_visible_returns_visible_match() -> None:
    hidden = _FakeLocatorItem(visible=False, name="hidden")
    visible = _FakeLocatorItem(visible=True, name="visible")
    locator = _FakeLocatorGroup([hidden, visible])

    selected = BaseComponent._pick_visible(cast(Any, locator))

    # _pick_visible calls locator(":visible").first which filters to visible items
    assert selected is visible


def test_find_does_not_reresovle_root(monkeypatch: pytest.MonkeyPatch) -> None:
    visible = _FakeLocatorItem(visible=True, name="visible")
    locator = _FakeLocatorGroup([visible])
    component = BaseComponent(cast(Any, locator))

    # Capture the root after construction
    root_after_init = component.root

    # Call find() - it should NOT re-resolve root
    result = component.find("some-selector")

    # Root should remain the same object (no re-resolution)
    assert component.root is root_after_init
    # Result should be from chaining on root
    assert result is not None


def test_pointer_click_uses_visible_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    hidden = _FakeLocatorItem(visible=False, name="hidden")
    visible = _FakeLocatorItem(visible=True, name="visible")
    locator = _FakeLocatorGroup([hidden, visible])
    component = BaseComponent(cast(Any, locator))

    monkeypatch.setattr(
        "framework.base.page_objects.base_component.expect",
        lambda target: _FakeExpectation(target),
    )

    component.pointer_click(cast(Any, locator))

    # The :visible filter on the group returns visible items, so visible gets clicked
    assert visible.click_calls == 1
    assert visible.scroll_calls == 1
    assert hidden.click_calls == 0


def test_wait_visible_resolves_root(monkeypatch: pytest.MonkeyPatch) -> None:
    visible = _FakeLocatorItem(visible=True, name="visible")
    locator = _FakeLocatorGroup([visible])
    component = BaseComponent(cast(Any, locator))

    monkeypatch.setattr(
        "framework.base.page_objects.base_component.expect",
        lambda target: _FakeExpectation(target),
    )

    component.wait_visible(timeout=300)

    # After wait_visible, root should be re-picked via _pick_visible
    assert component.root is visible
