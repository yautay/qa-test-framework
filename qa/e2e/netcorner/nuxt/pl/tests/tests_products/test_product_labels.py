from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import ListingProductTileComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Kafelki listingu zawierają etykiety promocyjne")
def test_product_labels(page, runtime_env):
    listings_data = first_available_laptop_case()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()

    tiles = listing.content.content.root.locator("[data-name='listingTile']")
    tile_count = min(tiles.count(), 10)
    has_label = False
    for index in range(tile_count):
        tile = ListingProductTileComponent(tiles.nth(index))
        if tile.get_promotion_message():
            has_label = True
            break

    assert has_label, "Nie znaleziono etykiety promocyjnej na żadnym z pierwszych kafelków listingu."
