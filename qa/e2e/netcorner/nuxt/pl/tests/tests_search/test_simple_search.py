from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e, pytest.mark.search]


@allure.feature("Wyszukiwanie")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("phrase", ["amd", "ładowark"], ids=["search_amd", "search_ladowarka"])
@pytest.mark.scenario("Proste wyszukiwanie frazy — niepusta lista wyników")
def test_simple_search(page, runtime_env, phrase):
    """Weryfikuje, że wyszukiwanie dowolnej frazy zwraca niepustą listę produktów.

    Migracja z: SearchTestsNUXT/TestSimpleSearch.py
    """
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH)
    home.wait_loaded()

    home.header.search_bar.fill_phrase(phrase)
    home.header.search_bar.submit()

    listing = ListingPage(page, runtime_env.base_url).wait_loaded()
    count = listing.content.content.count()

    assert count > 0, (
        f"Wyszukiwanie frazy '{phrase}' zwróciło pustą listę produktów."
    )
