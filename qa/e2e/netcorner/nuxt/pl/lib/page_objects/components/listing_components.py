from __future__ import annotations

from playwright.sync_api import Locator

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step


class ListingFiltersComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Sekcja filtrów listingów")



class ListingSortingComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Sekcja sortowania listingów")



class ListingContentComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Sekcja zawartości listingów")


