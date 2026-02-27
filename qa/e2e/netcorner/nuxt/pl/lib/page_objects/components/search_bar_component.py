from __future__ import annotations

from playwright.sync_api import expect, Locator
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class SearchBarComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="SearchBar")
        self.__input = self.find('[placeholder="Wpisz czego szukasz"]')
        self.__submit = self.find('[title="search-button"]')

    def fill_phrase(self, phrase: str) -> "SearchBarComponent":
        self.safe_type(self.__input, phrase)
        return self

    def submit(self) -> None:
        self.safe_click(self.__submit)

    def assert_value(self, expected: str) -> None:
        expect(self.__input).to_have_value(expected)