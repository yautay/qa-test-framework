from __future__ import annotations

from enum import StrEnum

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step


class ListingFiltersComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='filtersDesktop']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR).first, name="Listing Filters Component")

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
    class SortOption(StrEnum):
        DEFAULT = "Domyślnie"
        PRICE_ASC = "Po cenie rosnąco"
        PRICE_DESC = "Po cenie malejąco"
        NAME_ASC = "Alfabetycznie A-Z"
        NAME_DESC = "Alfabetycznie Z-A"

    class AvailabilityOption(StrEnum):
        ANY = "Nieistotne"
        MAIN_WAREHOUSE = "Poznań Komorniki - Magazyn Główny"
        SHIPPING_WAREHOUSE = "Magazyn wysyłkowy"
        EXTERNAL_WAREHOUSE = "Zewnętrzny magazyn"
        ANY_STORE = "Dowolny salon"
        GDYNIA = "Gdynia - salon firmowy"
        GNIEZNO = "Gniezno - salon firmowy"
        POZNAN_PLAZA = "Poznań CH Plaza - salon firmowy"
        POZNAN_OUTLET_KOMORNIKI = "Poznań Outlet Komorniki - salon firmowy"
        POZNAN_POSNANIA = "Poznań, CH Posnania - salon firmowy"
        POZNAN_MARCELIN = "Poznań, King Cross Marcelin - salon  firmowy"
        WARSAW_ARKADIA = "Warszawa CH Westfield Arkadia - salon firmowy"

    ROOT_SELECTOR = "[data-role='barFilters']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR).first, name="Listing Sorting Component")

        self.__sort_dropdown = self.find("[data-role='selectInputArea']")
        self.__sort_options_container = self.__sort_dropdown.locator("xpath=following-sibling::*[1]")
        self.__show_unavailable_checkbox = self.find("#checkboxShowUnavailable")

    # actions
    @step("Wybieram opcję z listy sortowania: {option}")
    def select_sort_option(self, option: ListingSortingComponent.SortOption) -> None:
        option_label = option.value if hasattr(option, "value") else str(option)
        self.safe_click(self.__sort_dropdown)
        self.safe_click(self.__sort_options_container.get_by_text(option_label, exact=True).first)
        self.root.page.wait_for_load_state("domcontentloaded")

    @step("Wybieram opcję z listy dostępności: {option}")
    def select_availability_option(self, option: ListingSortingComponent.AvailabilityOption) -> None:
        option_label = option.value if hasattr(option, "value") else str(option)
        availability_input = self.root.page.locator("#pageContentWrapper [data-role='barFilters'] #barFilters").first
        availability_results = self.root.page.locator(
            "#pageContentWrapper [data-role='barFilters'] #autocomplete-results"
        ).first
        self.safe_click(availability_input, timeout=15_000)
        self.safe_click(availability_results.locator("li").filter(has_text=option_label).first, timeout=15_000)

    @step("Ustawiam checkbox 'Pokaż produkty niedostępne' na: {checked}")
    def set_show_unavailable(self, checked: bool) -> None:
        if self.__show_unavailable_checkbox.is_checked() != checked:
            self.safe_click(self.__show_unavailable_checkbox)


class ListingContentComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='listingContent']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR).first, name="Sekcja zawartości listingów")
