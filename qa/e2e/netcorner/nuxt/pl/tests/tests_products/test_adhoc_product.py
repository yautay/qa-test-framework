from __future__ import annotations

import re

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Scenariusz produktu ad-hoc — alfa")
def test_adhoc_product(page, runtime_env):
    listings_data = first_available_laptop_case()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()

    adhoc_marker = listing.content.content.root.get_by_text(re.compile(r"ad\s*[- ]?hoc|niestandard|konfigurow", re.IGNORECASE))
    if adhoc_marker.count() == 0:
        pytest.skip("Brak widocznego produktu ad-hoc/niestandardowego na aktualnym listingu.")

    assert adhoc_marker.first.is_visible(), "Wykryty marker ad-hoc nie jest widoczny dla użytkownika."
