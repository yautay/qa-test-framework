from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.dom_capture import capture_page_dom
from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.timeouts import UI_ACTION_MS
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import (
    get_visible_text,
    normalize_price,
    price_text_to_float,
    strip_prefix,
)
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

    @step("Aplikuję filtr: {name}")
    def apply_filter_by_name(self, name: str) -> Self:
        filter_label = self.root.get_by_text(name, exact=True).first
        expect(filter_label).to_be_visible(
            timeout=self.DEFAULT_TIMEOUT
        ), f"Filtr '{name}' nie istnieje na listingu — sprawdź URL lub dostępność filtra na środowisku."
        self.pointer_click(filter_label)
        self.root.page.wait_for_load_state("networkidle", timeout=UI_ACTION_MS)
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
        page = self.root.page
        # Open the dropdown (no navigation).
        self.pointer_click(self.__sort_dropdown)
        # Click the chosen option — triggers a SPA route change (Vue Router
        # pushState).  expect_navigation with domcontentloaded does NOT work
        # here because domcontentloaded already fired on initial load.  Instead
        # we use networkidle which waits until the data fetch triggered by the
        # route change has settled.
        option_locator = self.__sort_options_container.get_by_text(option_label, exact=True).first
        self.pointer_click(option_locator)
        page.wait_for_load_state("networkidle", timeout=UI_ACTION_MS)
        # Confirm listing content and at least one tile are visible.
        listing_content = page.locator("[data-name='listingContent']")
        expect(listing_content).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        expect(listing_content.locator("[data-name='listingTile']").first).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        return self

    @step("Wybieram opcję z listy dostępności: {option}")
    def select_availability_option(self, option: ListingSortingComponent.AvailabilityOption) -> Self:
        option_label = option.value
        self.__select_from_custom_dropdown(self.__availability_input, self.__availability_results, option_label)
        expect(self.__availability_input).to_have_value(option_label, timeout=UI_ACTION_MS)
        return self

    @step("Ustawiam checkbox 'Pokaż produkty niedostępne' na: {checked}")
    def set_show_unavailable(self, checked: bool) -> Self:
        if self.__show_unavailable_checkbox.is_checked() != checked:
            with self.root.page.expect_navigation(wait_until="domcontentloaded", timeout=self.DEFAULT_TIMEOUT):
                self.pointer_click(self.__show_unavailable_checkbox)
            listing_content = self.root.page.locator("[data-name='listingContent']")
            expect(listing_content).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
            expect(listing_content.locator("[data-name='listingTile']").first).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
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
    min_qty: int | None


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
            min_qty=self.get_min_qty(),
        )

    def get_min_qty(self) -> int | None:
        min_qty_el = self.root.locator("[data-min-qty]").first
        if min_qty_el.count() == 0 or not min_qty_el.is_visible():
            return None
        raw = min_qty_el.get_attribute("data-min-qty")
        try:
            return int(raw) if raw is not None else None
        except ValueError:
            return None


class ListingContentComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='listingContent']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Sekcja zawartości listingów")

        self.__tiles = self.find("[data-name='listingTile']")

    def count(self) -> int:
        return self.__tiles.count()

    def wait_for_tiles(self, timeout: int = 15_000) -> None:
        """Wait until at least one listing tile is visible.

        Nuxt pages undergo client-side hydration after domcontentloaded, during
        which SSR tiles are briefly removed and re-rendered.  Callers that need
        an accurate ``count()`` must wait here first.
        """
        expect(self.__tiles.first).to_be_visible(timeout=timeout)

    def wait_for_tiles_stable(self, timeout: int = 15_000, interval_ms: int = 500) -> None:
        """Wait until the tile count is stable across two consecutive reads.

        After a SPA sort/filter change Vue briefly shows stale SSR tiles while
        fetching new data.  Simply waiting for networkidle or tile visibility is
        not enough — the tile locator resolves to old nodes that are still in the
        DOM.  This method polls until the count stays the same twice in a row,
        which reliably signals that the re-render cycle is complete.
        """
        import time as _time
        deadline = _time.monotonic() + timeout / 1000
        prev = self.__tiles.count()
        while _time.monotonic() < deadline:
            _time.sleep(interval_ms / 1000)
            current = self.__tiles.count()
            if current > 0 and current == prev:
                return
            prev = current
        # Final check — at least one tile must be visible
        expect(self.__tiles.first).to_be_visible(timeout=self.DEFAULT_TIMEOUT)

    @step("Pobieram ceny finalne wszystkich produktów na listingu")
    def get_all_final_prices(self) -> list[float]:
        """Returns final prices of all visible listing tiles as floats for sort comparison."""
        self.wait_for_tiles_stable()
        count = self.__tiles.count()
        prices: list[float] = []
        for i in range(count):
            price_el = self.__tiles.nth(i).locator("[data-price-type='final']").first
            raw = (price_el.text_content() or "").strip()
            prices.append(price_text_to_float(raw))
        return prices

    @step("Pobieram nazwy wszystkich produktów na listingu")
    def get_all_product_names(self) -> list[str]:
        """Returns product names (h2) of all visible listing tiles for sort comparison."""
        self.wait_for_tiles_stable()
        count = self.__tiles.count()
        names: list[str] = []
        for i in range(count):
            name_el = self.__tiles.nth(i).locator("a[title] h2").first
            names.append((name_el.text_content() or "").strip().lower())
        return names

    @step("Pobieram kody systemowe wszystkich produktów na listingu")
    def get_all_system_codes(self) -> list[str]:
        count = self.__tiles.count()
        codes: list[str] = []
        for i in range(count):
            tile = ListingProductTileComponent(self.__tiles.nth(i))
            code = tile.get_system_code().strip()
            if code:
                codes.append(code)
        return codes

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

    @step("Wyszukuję pierwszy produkt o statusie dostępności z pominięciem kodów systemowych")
    def find_first_product_by_shipping_status_excluding_system_codes(
        self,
        shipping_status: AvailabilityStatus,
        excluded_system_codes: set[str],
        skip_min_qty_gt_one: bool = False,
    ) -> ListingProductTileComponent | None:
        tile_count = self.count()
        for index in range(tile_count):
            product_tile = ListingProductTileComponent(self.__tiles.nth(index))
            if product_tile.get_shipping_status() != shipping_status:
                continue
            if product_tile.get_system_code() in excluded_system_codes:
                continue
            if skip_min_qty_gt_one:
                min_qty = product_tile.get_min_qty()
                if min_qty is not None and min_qty > 1:
                    continue
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
        capture_page_dom(
            self.root.page,
            event="listing_pagination_next",
            page_id="netcorner.pl.listing.category",
        )
        return True
