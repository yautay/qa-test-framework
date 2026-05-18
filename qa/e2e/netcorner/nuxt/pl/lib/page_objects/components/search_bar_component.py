from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class SearchBarComponent(BaseComponent):
    ROOT_SELECTOR = '[data-role="searchComponent"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="SearchBar")
        self.__input = self.find('[placeholder="Wpisz czego szukasz"]')
        self.__submit = self.find('[title="search-button"]')
        # Suggestions overlay — rendered by JS after typing; lives inside the component root
        self.__suggestions = self.find("[data-name='searchComponentResults']")

    @step("Wpisuję frazę wyszukiwania: {phrase}")
    def fill_phrase(self, phrase: str) -> Self:
        self.safe_type(self.__input, phrase)
        return self

    @step("Przesyłam zapytanie wyszukiwania")
    def submit(self) -> None:
        self.pointer_click(self.__submit)

    @step("Sprawdzam, czy w polu wyszukiwania jest: {expected}")
    def assert_value(self, expected: str) -> None:
        expect(self.__input).to_have_value(expected)

    # --- search suggestions ---

    @step("Czekam na pojawienie się podpowiedzi wyszukiwania")
    def wait_for_suggestions(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__suggestions).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność sekcji produktów w podpowiedziach")
    def expect_suggestion_products_section_visible(self, timeout_ms: int = 10_000) -> Self:
        section = self.__suggestions.locator("div").filter(has_text="Produkty").first
        expect(section).to_be_visible(timeout=timeout_ms)
        return self

    @step("Pobieram liczbę podpowiedzi produktowych")
    def get_suggestion_product_count(self) -> int:
        """Returns the number of product suggestion links (links to /product/)."""
        return self.__suggestions.locator("a[href*='/product/']").count()

    @step("Pobieram nazwy produktów w podpowiedziach")
    def get_suggestion_product_names(self) -> list[str]:
        """Returns visible text content of product suggestion links."""
        links = self.__suggestions.locator("a[href*='/product/']")
        count = links.count()
        return [(links.nth(i).text_content() or "").strip() for i in range(count)]

    @step("Sprawdzam, czy podpowiedzi zawierają sekcję producenta")
    def has_producer_section(self) -> bool:
        """Returns True if a producer link is visible in suggestions."""
        return self.__suggestions.locator("a[href*='/producer/']").count() > 0

    @step("Pobieram href linku producenta w podpowiedziach")
    def get_producer_link_href(self) -> str:
        """Returns href of the first producer link in suggestions."""
        link = self.__suggestions.locator("a[href*='/producer/']").first
        return link.get_attribute("href") or ""
