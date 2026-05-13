from __future__ import annotations

import re

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Filtrowanie listingu po Sezam — alfa")
def test_products_list_sezam_filter(page, runtime_env):
    listings_data = first_available_laptop_case()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()

    sezam_label = listing.content.filters.root.get_by_text(re.compile(r"sezam", re.IGNORECASE))
    if sezam_label.count() == 0:
        pytest.skip("Brak filtra Sezam na aktualnym listingu środowiska testowego.")

    listing.content.filters.expand_all_filters()
    listing.content.filters.pointer_click(sezam_label.first)
    listing.content.content.wait_for_tiles()
    assert listing.content.content.count() > 0, "Po zastosowaniu filtra Sezam nie znaleziono produktów."
