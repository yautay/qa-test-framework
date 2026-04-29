from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, expect


class BaseComponent:
    DEFAULT_TIMEOUT = 10_000

    def __init__(self, root: Locator, name: str = "Component"):
        self._root_candidates = root
        self.root = self._pick_visible(root)
        self.name = name

    @staticmethod
    def _pick_visible(locator: Locator) -> Locator:
        """Return first match — visibility is deferred to expect assertions."""
        return locator.first

    def wait_visible(self, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        expect(self._root_candidates.first).to_be_visible(timeout=t)
        return self

    def wait_hidden(self, timeout: int | None = None) -> Self:
        expect(self.root).to_be_hidden(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def assert_visible(self) -> Self:
        target = self._resolve_visible_root(timeout=self.DEFAULT_TIMEOUT)
        expect(target).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        return self

    def assert_hidden(self) -> Self:
        expect(self.root).to_be_hidden(timeout=self.DEFAULT_TIMEOUT)
        return self

    def pointer_click(self, locator: Locator, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.first
        expect(target).to_be_visible(timeout=t)
        expect(target).to_be_enabled(timeout=t)
        target.scroll_into_view_if_needed()
        target.click(timeout=t)
        return self

    def non_pointer_click(self, locator: Locator, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.first
        expect(target).to_be_visible(timeout=t)
        expect(target).to_be_enabled(timeout=t)
        target.scroll_into_view_if_needed()
        target.evaluate("node => node.click()")
        return self

    def safe_fill(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.first
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.fill(value, timeout=t)
        return self

    def safe_type(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = locator.first
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.type(value, timeout=t)
        return self

    def should_have_text(self, locator: Locator, text: str) -> Self:
        expect(locator).to_have_text(text, timeout=self.DEFAULT_TIMEOUT)
        return self

    def find(self, selector: str) -> Locator:
        return self.root.locator(selector)

    def _resolve_visible_root(self, *, timeout: int) -> Locator:
        return self._pick_visible(self._root_candidates)

    def sleep(self, ms: int) -> Self:
        if ms < 0:
            raise ValueError("ms must be >= 0")
        self.root.page.wait_for_timeout(ms)
        return self
