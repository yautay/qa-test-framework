from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import BrowserContext, Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.lib.step_api import step_context
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import ListingProductData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.product_components import ProductPriceData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listings_data_models import ListingsData


@dataclass(frozen=True, slots=True)
class SelectProductData:
    listing_data: ListingProductData
    product_page_data: ProductPriceData | None


class SelectProductWrappers:
    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.__page = page
        self.__context = context
        self.__runtime_env = runtime_env
        self.__data = []

    def select_test_product(
        self,
        listings_data: ListingsData | None = None,
        add_to_cart: bool = True,
    ) -> SelectProductData | None:
        if listings_data is None:
            return None

        with step_context(f"Wchodzę na URL kategorii: /{listings_data.category_url}"):
            listing_page = ListingPage(
                self.__page,
                f"{self.__runtime_env.base_url}/{listings_data.category_url}",
            )
            content_section = listing_page.content
            listing_page.open().wait_loaded()

        if listings_data.filters:
            with step_context("Rozwijam wszystkie filtry"):
                listing_page.content.filters.expand_all_filters()

        with step_context("Ustawiam parametry sortowania i dostępności"):
            content_section.sorting.select_sort_option(content_section.sorting.SortOption.PRICE_ASC)
            content_section.sorting.select_availability_option(
                content_section.sorting.AvailabilityOption.MAIN_WAREHOUSE
            )
            content_section.sorting.set_show_unavailable(False)

        expected_status = listings_data.product_availability_status
        with step_context(f"Szukam produktu o statusie: {expected_status.status}"):
            result = listing_page.open_first_product_by_shipping_status(expected_status)
            if result is None:
                raise AssertionError(
                    f"Nie znaleziono produktu o statusie dostępności: '{expected_status.status}'."
                )

            selected_product_data, product_page = result

        product_page_data = None
        if add_to_cart:
            with step_context("Dodaję wybrany produkt do koszyka"):
                product_page_data = product_page.add_to_cart()

        return SelectProductData(
            listing_data=selected_product_data,
            product_page_data=product_page_data,
        )
