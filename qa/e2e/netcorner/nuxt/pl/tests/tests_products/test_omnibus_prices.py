from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.omnibus_price_component import OmnibusPriceComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Listing wyświetla ceny omnibus dla części produktów")
def test_omnibus_prices(page, runtime_env):
    listings_data = first_available_laptop_case()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()

    prices = OmnibusPriceComponent(listing.content.content.root).get_prices()
    assert prices, "Na listingu nie znaleziono żadnej ceny omnibus."
    assert all(price.strip() for price in prices), "Wykryto pustą wartość ceny omnibus."
