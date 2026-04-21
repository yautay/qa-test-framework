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

    @step("Wpisuję frazę wyszukiwania: {phrase}")
    def fill_phrase(self, phrase: str) -> Self:
        self.safe_type(self.__input, phrase)
        return self

    @step("Przesyłam zapytanie wyszukiwania")
    def submit(self) -> None:
        self.safe_click(self.__submit)

    @step("Sprawdzam, czy w polu wyszukiwania jest: {expected}")
    def assert_value(self, expected: str) -> None:
        expect(self.__input).to_have_value(expected)
