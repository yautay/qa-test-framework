from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, expect


class BaseComponent:
    DEFAULT_TIMEOUT = 30_000

    def __init__(self, root: Locator, name: str = "Component"):
        self.root = self.first_visible(root)
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
        expect(self.root).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def wait_hidden(self, timeout: int | None = None) -> Self:
        expect(self.root).to_be_hidden(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def assert_visible(self) -> None:
        expect(self.root).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

    def assert_hidden(self) -> None:
        expect(self.root).to_be_hidden(timeout=self.DEFAULT_TIMEOUT)

    def safe_click(self, locator: Locator, *, timeout: int | None = None) -> None:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self.first_visible(locator)
        expect(target).to_be_visible(timeout=t)
        expect(target).to_be_enabled(timeout=t)
        target.scroll_into_view_if_needed()
        target.click(timeout=t)

    def safe_fill(self, locator: Locator, value: str, *, timeout: int | None = None) -> None:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self.first_visible(locator)
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.fill(value, timeout=t)

    def safe_type(self, locator: Locator, value: str, *, timeout: int | None = None) -> None:
        t = timeout or self.DEFAULT_TIMEOUT
        target = self.first_visible(locator)
        expect(target).to_be_visible(timeout=t)
        target.scroll_into_view_if_needed()
        target.type(value, timeout=t)

    def should_have_text(self, locator: Locator, text: str) -> None:
        expect(locator).to_have_text(text, timeout=self.DEFAULT_TIMEOUT)

    def find(self, selector: str) -> Locator:
        return self.root.locator(selector)

    def sleep(self, ms: int) -> Self:
        if ms < 0:
            raise ValueError("ms must be >= 0")
        self.root.page.wait_for_timeout(ms)
        return self
