from __future__ import annotations

import time
from typing import Self

from playwright.sync_api import Locator, expect


class BaseComponent:
    DEFAULT_TIMEOUT = 10_000

    def __init__(self, root: Locator, name: str = "Component"):
        self._root_candidates = root
        self.root = self.first_visible(self._root_candidates)
        self.name = name

    @staticmethod
    def first_visible(locator: Locator) -> Locator:
        try:
            count = locator.count()
        except Exception:
            return locator.first

        for index in range(count):
            candidate = locator.nth(index)
            try:
                if candidate.is_visible():
                    return candidate
            except Exception:
                continue

        return locator.first

    def wait_visible(self, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self._resolve_visible_root(timeout=t)
        expect(target).to_be_visible(timeout=t)
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
        target = self.first_visible(locator)
        expect(target).to_be_visible(timeout=t)
        expect(target).to_be_enabled(timeout=t)
        target.scroll_into_view_if_needed()
        target.click(timeout=t)
        return self

    def non_pointer_click(self, locator: Locator, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self.first_visible(locator)
        expect(target).to_be_visible(timeout=t)
        expect(target).to_be_enabled(timeout=t)
        target.scroll_into_view_if_needed()
        target.evaluate("node => node.click()")
        return self

    def safe_fill(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self.first_visible(locator)
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.fill(value, timeout=t)
        return self

    def safe_type(self, locator: Locator, value: str, *, timeout: int | None = None) -> Self:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self.first_visible(locator)
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.type(value, timeout=t)
        return self

    def should_have_text(self, locator: Locator, text: str) -> Self:
        expect(locator).to_have_text(text, timeout=self.DEFAULT_TIMEOUT)
        return self

    def find(self, selector: str) -> Locator:
        self.root = self.first_visible(self._root_candidates)
        return self.root.locator(selector)

    def _resolve_visible_root(self, *, timeout: int) -> Locator:
        self.root = self.first_visible(self._root_candidates)
        try:
            if self.root.is_visible():
                return self.root
        except Exception:
            pass

        deadline = time.monotonic() + (timeout / 1000)
        while time.monotonic() < deadline:
            self.root = self.first_visible(self._root_candidates)
            try:
                if self.root.is_visible():
                    return self.root
            except Exception:
                pass
            time.sleep(0.1)

        return self.root

    def sleep(self, ms: int) -> Self:
        if ms < 0:
            raise ValueError("ms must be >= 0")
        self.root.page.wait_for_timeout(ms)
        return self
