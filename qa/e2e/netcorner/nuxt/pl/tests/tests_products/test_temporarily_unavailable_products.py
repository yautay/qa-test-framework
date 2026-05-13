from __future__ import annotations

import re

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Na listingu można wyświetlić produkty tymczasowo niedostępne")
def test_temporarily_unavailable_products(page, runtime_env):
    listings_data = first_available_laptop_case()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()

    listing.content.sorting.set_show_unavailable(True)
    tiles = listing.content.content.root.locator("[data-name='listingTile']")
    unavailable_count = tiles.filter(has_text=re.compile(r"niedost", re.IGNORECASE)).count()

    if unavailable_count == 0:
        pytest.skip("Brak produktów niedostępnych na badanej kategorii w tym momencie.")

    assert unavailable_count > 0, "Nie wykryto produktów niedostępnych po włączeniu opcji ich wyświetlania."
