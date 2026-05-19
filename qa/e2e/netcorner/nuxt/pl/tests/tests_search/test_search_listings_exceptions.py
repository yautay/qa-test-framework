from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import AdminSettingsExceptionListPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_search]


@allure.feature("Wyszukiwanie")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("url_suffix", ["", "?test=1"], ids=["html_cache_on", "html_cache_off"])
@pytest.mark.scenario("Kategorie z wyjątków konfiguracji renderują niepusty listing")
def test_search_listings_exceptions(page, runtime_env, admin_panel, url_suffix: str):
    admin_panel.open_admin()
    entries = (
        AdminSettingsExceptionListPage(page, admin_panel.admin_env.base_url)
        .navigate_to()
        .get_category_entries(limit=4)
    )
    assert entries, "Admin nie zwrócił żadnych wyjątków konfiguracji kategorii do testu listingów."

    for entry in entries:
        listing = ListingPage(page, runtime_env.base_url)
        listing.open(f"/category/{entry.category_id}{url_suffix}").wait_loaded()

        count = listing.content.content.count()
        assert count > 0, (
            f"Listing kategorii z wyjątku '{entry.config_name}' "
            f"(id={entry.category_id}) jest pusty dla suffixu '{url_suffix}'."
        )

        system_codes = listing.content.content.get_all_system_codes()
        product_names = listing.content.content.get_all_product_names()
        prices = listing.content.content.get_all_final_prices()

        assert system_codes, (
            f"Listing kategorii id={entry.category_id} nie zwrócił żadnych kodów systemowych produktów."
        )
        assert product_names, (
            f"Listing kategorii id={entry.category_id} nie zwrócił żadnych nazw produktów."
        )
        assert prices and all(price > 0 for price in prices), (
            f"Listing kategorii id={entry.category_id} zwrócił nieprawidłowe ceny: {prices}."
        )
