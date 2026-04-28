from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text, normalize_price, strip_prefix
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import (
    AvailabilityStatus,
    AvailabilityStatuses,
)


class ListingFiltersComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='filtersDesktop']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Listing Filters Component")

        self._show_more_accordion_triggers = self.find("[data-name='accordionTrigger']").filter(has_text="Pokaż więcej")
        self._show_all_features_buttons = self.find("button").filter(has_text="Pokaż wszystkie cechy")

    @step("Rozwijam wszystkie sekcje 'Pokaż więcej'")
    def __expand_all_show_more_sections(self) -> None:
        triggers = self._show_more_accordion_triggers
        count = triggers.count()

        for index in range(count):
            trigger = triggers.nth(index)

            if trigger.is_visible():
                self.pointer_click(trigger)

    @step("Klikam przycisk 'Pokaż wszystkie cechy'")
    def __click_all_show_all_features_buttons(self) -> None:
        buttons = self._show_all_features_buttons
        count = buttons.count()

        for index in range(count):
            button = buttons.nth(index)

            if button.is_visible():
                self.pointer_click(button)

    @step("Rozwijam wszystkie dostępne filtry")
    def expand_all_filters(self) -> Self:
        self.__expand_all_show_more_sections()
        self.__click_all_show_all_features_buttons()
        return self


class SortOptions(StrEnum):
    DEFAULT = "Domyślnie"
    PRICE_ASC = "Po cenie rosnąco"
    PRICE_DESC = "Po cenie malejąco"
    NAME_ASC = "Alfabetycznie A-Z"
    NAME_DESC = "Alfabetycznie Z-A"


class AvailabilityOptions(StrEnum):
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


class ListingSortingComponent(BaseComponent):
    SortOption = SortOptions
    AvailabilityOption = AvailabilityOptions

    ROOT_SELECTOR = "[data-role='barFilters']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Listing Sorting Component")

        self.__sort_dropdown = self.find("[data-role='selectInputArea']").first
        self.__sort_options_container = self.__sort_dropdown.locator("xpath=following-sibling::*[1]").first
        self.__availability_input = self.find("#barFilters").first
        self.__availability_results = self.find("#autocomplete-results").first
        self.__show_unavailable_checkbox = self.find("#checkboxShowUnavailable")

    def __select_from_custom_dropdown(
        self, trigger: Locator, options_container: Locator, option_label: str, timeout: int = 10_000
    ) -> None:
        self.pointer_click(trigger, timeout=timeout)
        self.pointer_click(options_container.get_by_text(option_label, exact=True).first, timeout=timeout)

    # actions
    @step("Wybieram opcję z listy sortowania: {option}")
    def select_sort_option(self, option: ListingSortingComponent.SortOption) -> Self:
        option_label = option.value
        self.__select_from_custom_dropdown(self.__sort_dropdown, self.__sort_options_container, option_label)
        expect(self.__sort_dropdown).to_contain_text(option_label, timeout=15_000)
        return self

    @step("Wybieram opcję z listy dostępności: {option}")
    def select_availability_option(self, option: ListingSortingComponent.AvailabilityOption) -> Self:
        option_label = option.value
        self.__select_from_custom_dropdown(self.__availability_input, self.__availability_results, option_label)
        expect(self.__availability_input).to_have_value(option_label, timeout=15_000)
        return self

    @step("Ustawiam checkbox 'Pokaż produkty niedostępne' na: {checked}")
    def set_show_unavailable(self, checked: bool) -> Self:
        if self.__show_unavailable_checkbox.is_checked() != checked:
            self.pointer_click(self.__show_unavailable_checkbox)
            expect(self.root.page.locator("[data-name='listingContent']")).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        return self

    def is_show_unavailable_checked(self) -> bool:
        return self.__show_unavailable_checkbox.is_checked()


@dataclass(frozen=True)
class ListingProductData:
    product_title: str
    system_code: str
    final_price: str
    promotion_message: bool
    shipping_status: AvailabilityStatus | None


class ListingProductTileComponent(BaseComponent):
    def __init__(self, scope: Locator) -> None:
        super().__init__(scope, name="Kafelek produktu na listingu")

        self.__product_title = self.find("a[title] h2").first
        self.__system_code = self.find("p").filter(has_text="Kod systemowy:").first
        self.__final_price = self.find("[data-price-type='final']").first
        self.__promotion_message = (
            self.find("[data-name='promotion']").get_by_text("Ten produkt możesz kupić w promocji!").first
        )
        self.__shipping_status = self.find("[data-name='statusAvailable'] .font-semibold").first
        self.__see_more_button = (
            self.find("[data-name='listingTileActions']").get_by_role("button", name="Zobacz więcej").first
        )

    @step("Klikam w przycisk 'Zobacz więcej' dla produktu")
    def click_see_more(self) -> None:
        self.pointer_click(self.__see_more_button)

    def get_product_title(self) -> str:
        return get_visible_text(self.__product_title)

    def get_system_code(self) -> str:
        return strip_prefix(get_visible_text(self.__system_code), "Kod systemowy:")

    def get_final_price(self) -> str:
        return normalize_price(get_visible_text(self.__final_price))

    def get_promotion_message(self) -> bool:
        promotion = self.__promotion_message.first
        return promotion.count() > 0 and promotion.is_visible()

    def get_shipping_status(self) -> AvailabilityStatus | None:
        status_text = get_visible_text(self.__shipping_status)
        if not status_text:
            return None
        try:
            return AvailabilityStatuses.from_status_text(status_text)
        except ValueError:
            return None

    def get_data(self) -> ListingProductData:
        return ListingProductData(
            product_title=self.get_product_title(),
            system_code=self.get_system_code(),
            final_price=self.get_final_price(),
            promotion_message=self.get_promotion_message(),
            shipping_status=self.get_shipping_status(),
        )


class ListingContentComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='listingContent']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Sekcja zawartości listingów")

        self.__tiles = self.find("[data-name='listingTile']")

    def count(self) -> int:
        return self.__tiles.count()

    @step("Wyszukuję pierwszy produkt o statusie dostępności: {shipping_status}")
    def find_first_product_by_shipping_status(
        self, shipping_status: AvailabilityStatus
    ) -> ListingProductTileComponent | None:
        tile_count = self.count()
        for index in range(tile_count):
            product_tile = ListingProductTileComponent(self.__tiles.nth(index))
            if product_tile.get_shipping_status() == shipping_status:
                return product_tile
        return None

    @step("Przechodzę do kolejnej strony listingu")
    def go_to_next_page(self) -> bool:
        next_page_link = self.find("a[aria-label='nawiguj do następnej strony']").first
        if next_page_link.count() == 0:
            return False

        with self.root.page.expect_navigation(wait_until="domcontentloaded"):
            self.pointer_click(next_page_link)
        self.wait_visible()
        return True
