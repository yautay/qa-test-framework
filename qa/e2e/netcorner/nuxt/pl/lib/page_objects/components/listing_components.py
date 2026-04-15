from __future__ import annotations

from playwright.sync_api import Locator

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step


class ListingFiltersComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Listing Filters Component")

        self._show_more_accordion_triggers = self.find("[data-name='accordionTrigger']").filter(has_text="Pokaż więcej")
        self._show_all_features_buttons = self.find("button").filter(has_text="Pokaż wszystkie cechy")

    @step("Rozwijam wszystkie sekcje 'Pokaż więcej'")
    def __expand_all_show_more_sections(self) -> None:
        triggers = self._show_more_accordion_triggers
        count = triggers.count()

        for index in range(count):
            trigger = triggers.nth(index)

            if trigger.is_visible():
                self.safe_click(trigger)

    @step("Klikam przycisk 'Pokaż wszystkie cechy'")
    def __click_all_show_all_features_buttons(self) -> None:
        buttons = self._show_all_features_buttons
        count = buttons.count()

        for index in range(count):
            button = buttons.nth(index)

            if button.is_visible():
                self.safe_click(button)

    @step("Rozwijam wszystkie dostępne filtry")
    def expand_all_filters(self) -> None:
        self.__expand_all_show_more_sections()
        self.__click_all_show_all_features_buttons()


class ListingSortingComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Sekcja sortowania listingów")



class ListingContentComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Sekcja zawartości listingów")


