from __future__ import annotations

from playwright.sync_api import Locator, expect


class BaseComponent:
    DEFAULT_TIMEOUT = 5_000

    def __init__(self, root: Locator, name: str = "Component"):
        self.root = root
        self.name = name

    def wait_visible(self, timeout: int | None = None) -> BaseComponent:
        expect(self.root).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def wait_hidden(self, timeout: int | None = None) -> BaseComponent:
        expect(self.root).to_be_hidden(timeout=timeout or self.DEFAULT_TIMEOUT)
        return self

    def assert_visible(self) -> None:
        expect(self.root).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

    def assert_hidden(self) -> None:
        expect(self.root).to_be_hidden(timeout=self.DEFAULT_TIMEOUT)

    def safe_click(self, locator: Locator, *, timeout: int | None = None) -> None:
        t = timeout or self.DEFAULT_TIMEOUT
        expect(locator).to_be_visible(timeout=t)
        expect(locator).to_be_enabled(timeout=t)
        locator.scroll_into_view_if_needed()
        locator.click(timeout=t)

    def safe_fill(self, locator: Locator, value: str, *, timeout: int | None = None) -> None:
        t = timeout or self.DEFAULT_TIMEOUT
        expect(locator).to_be_visible(timeout=t)
        locator.scroll_into_view_if_needed()
        locator.fill(value, timeout=t)

    def safe_type(self, locator: Locator, value: str, *, timeout: int | None = None) -> None:
        t = timeout or self.DEFAULT_TIMEOUT
        expect(locator).to_be_visible(timeout=t)
        locator.scroll_into_view_if_needed()
        locator.type(value, timeout=t)

    def should_have_text(self, locator: Locator, text: str) -> None:
        expect(locator).to_have_text(text, timeout=self.DEFAULT_TIMEOUT)

    def find(self, selector: str) -> Locator:
        return self.root.locator(selector)
