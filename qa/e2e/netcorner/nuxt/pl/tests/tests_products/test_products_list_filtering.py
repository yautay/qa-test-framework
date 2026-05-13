from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import AvailabilityOptions
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Filtrowanie listingu po dostępności magazynu")
def test_products_list_filtering(page, runtime_env):
    listings_data = first_available_laptop_case()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()

    listing.content.filters.expand_all_filters()
    listing.content.sorting.select_availability_option(AvailabilityOptions.MAIN_WAREHOUSE)
    listing.content.content.wait_for_tiles()

    count = listing.content.content.count()
    assert count > 0, "Po zastosowaniu filtra dostępności listing nie zawiera żadnych produktów."
