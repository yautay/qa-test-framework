from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e]

# Listing laptopów z przedziałem cenowym 2000–6000 zł i filtrem dostępności (sh[]=205000).
# Ten URL jest punktem wejścia dla testów weryfikujących promocje "Produkty w niższej cenie"
# generowane przez zintegrowany system promocyjny.
_LAPTOPS_DISCOUNTED_LISTING_URL = (
    "category/5022/laptopy.html"
    "?showBuyActiveOnly=1&pr10[]=2000&pr10[]=6000&sh[]=205000&filter=1"
)


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Filtrowanie listingu laptopów po promocji 'Produkty w niższej cenie'")
def test_products_list_sezam_filter(page, runtime_env):
    listing = ListingPage(page, f"{runtime_env.base_url}/{_LAPTOPS_DISCOUNTED_LISTING_URL}").open().wait_loaded()

    listing.content.filters.expand_all_filters()
    listing.content.filters.apply_filter_by_name("Produkty w niższej cenie")

    assert listing.content.content.count() > 0, (
        "Po zastosowaniu filtra 'Produkty w niższej cenie' nie znaleziono żadnych produktów na listingu."
    )
