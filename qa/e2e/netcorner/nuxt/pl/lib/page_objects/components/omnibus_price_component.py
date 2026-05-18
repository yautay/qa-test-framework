from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text


class OmnibusPriceComponent(BaseComponent):
    def __init__(self, scope: Page | Locator) -> None:
        root = scope if isinstance(scope, Locator) else scope.locator("body")
        super().__init__(root, name="Omnibus Price Component")
        self.__omnibus_prices = self.find("[data-price-type='omnibus']")

    @step("Odczytuję wszystkie ceny omnibus")
    def get_prices(self) -> list[str]:
        prices: list[str] = []
        for i in range(self.__omnibus_prices.count()):
            value = get_visible_text(self.__omnibus_prices.nth(i))
            if value:
                prices.append(value)
        return prices
