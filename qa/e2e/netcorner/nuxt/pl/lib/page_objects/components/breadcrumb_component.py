from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class BreadcrumbComponent(BaseComponent):
    """Breadcrumb navigation trail component.

    Wraps ``[data-name='breadcrumbs']`` and exposes the ordered list of
    breadcrumb labels and the current (last) item text.
    """

    ROOT_SELECTOR = "[data-name='breadcrumbs']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Breadcrumb")
        self.__items = self.find("a")

    @step("Sprawdzam widoczność breadcrumb")
    def expect_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.root).to_be_visible(timeout=timeout_ms)
        return self

    @step("Pobieram teksty wszystkich pozycji breadcrumb")
    def get_all_texts(self) -> list[str]:
        """Returns breadcrumb link labels in order (left-to-right)."""
        count = self.__items.count()
        return [(self.__items.nth(i).text_content() or "").strip() for i in range(count)]

    @step("Pobieram tekst ostatniej pozycji breadcrumb")
    def get_current_page_text(self) -> str:
        """Returns the text of the last (current page) breadcrumb item."""
        last = self.__items.filter(has=self.root.locator("[aria-current='page']")).first
        if last.count() == 0:
            # Fallback: last anchor
            count = self.__items.count()
            if count == 0:
                return ""
            return (self.__items.nth(count - 1).text_content() or "").strip()
        return (last.text_content() or "").strip()
