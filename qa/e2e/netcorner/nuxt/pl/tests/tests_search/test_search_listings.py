from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e, pytest.mark.search]

# ---------------------------------------------------------------------------
# Key category URLs — mirrors CommonData.key_categories()
# expected_h1_fragment: substring of the page H1 (case-insensitive)
#   NOTE: listing pages have no breadcrumb component (client-side only).
#         H1 from [data-name='listingHeader'] is the canonical identifier.
# ---------------------------------------------------------------------------
_CATEGORY_CASES = [
    pytest.param("/category/5022/laptopy.html",                    "Laptopy",               id="cat_laptop"),
    pytest.param("/category/8011/czytniki-ebook.html",             "Czytniki e-book",       id="cat_ereader"),
    pytest.param("/category/2954/myszki.html",                     "Myszki",                id="cat_mouse"),
    pytest.param("/category/8874/dyski-zewnetrzne.html",           "Dyski zewnętrzne",      id="cat_ext_hdd"),
    pytest.param("/category/437/pamiec-ram.html",                  "RAM",                   id="cat_ram"),
    pytest.param("/category/1099/karty-graficzne.html",            "Karty graficzne",       id="cat_gpu"),
    pytest.param("/category/2371/routery.html",                    "Routery",               id="cat_router"),
    pytest.param("/category/1596/telefony.html",                   "Telefony",              id="cat_smartphone",
               marks=pytest.mark.skip(reason="?test=1 nie renderuje headerBar na galak.test dla tej kategorii — bug środowiska")),
    pytest.param("/category/1596/telefony,apple.html",             "iPhone",                id="cat_apple_phone"),
    pytest.param("/category/1596/telefony,samsung.html",           "Samsung",               id="cat_samsung_phone"),
    pytest.param("/category/5431/telewizory.html",                 "Telewizory",            id="cat_tv"),
    pytest.param("/category/1971/microsoft-windows-systemy-operacyjne.html", "Windows",    id="cat_win"),
    pytest.param("/category/686/pendrive.html",                    "Pendrive",              id="cat_pendrive"),
]

# ---------------------------------------------------------------------------
# Key producer URLs — mirrors CommonData.key_producers()
# ---------------------------------------------------------------------------
_PRODUCER_CASES = [
    pytest.param("/producer/7/apple.html",              "Apple",            id="prod_apple"),
    pytest.param("/producer/31/logitech.html",          "Logitech",         id="prod_logitech"),
    pytest.param("/producer/11/microsoft.html",         "Microsoft",        id="prod_microsoft"),
    pytest.param("/producer/4/intel.html",              "Intel",            id="prod_intel"),
    pytest.param("/producer/1/komputronik.html",        "Komputronik",      id="prod_komputronik"),
    pytest.param("/producer/514/msi.html",              "MSI",              id="prod_msi"),
    pytest.param("/producer/16/asus.html",              "Asus",             id="prod_asus"),
    pytest.param("/producer/19/acer.html",              "Acer",             id="prod_acer"),
    pytest.param("/producer/337/dell.html",             "Dell",             id="prod_dell"),
    pytest.param("/producer/122/razer.html",            "Razer",            id="prod_razer"),
    pytest.param("/producer/9/hp.html",                 "HP",               id="prod_hp"),
    pytest.param("/producer/22/california-access.html", "California Access", id="prod_california"),
]


def _open_listing(page, runtime_env, path: str) -> ListingPage:
    listing = ListingPage(page, runtime_env.base_url)
    listing.open(path).wait_loaded()
    return listing


# ---------------------------------------------------------------------------
# Category listing tests
# ---------------------------------------------------------------------------

@allure.feature("Wyszukiwanie — listingi kategorii")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("url,expected_h1_fragment", _CATEGORY_CASES)
@pytest.mark.scenario("Weryfikacja listingu kategorii i nagłówka H1")
def test_search_category_listing(page, runtime_env, url, expected_h1_fragment):
    """Weryfikuje, że strona kategorii zawiera produkty oraz że nagłówek H1
    zawiera oczekiwany fragment nazwy kategorii.

    Uwaga: listing pages nie renderują komponentu breadcrumb (jest client-only
    i nie pojawia się na stronach kategorii). Weryfikacja tytułu odbywa się
    przez H1 w [data-name='listingHeader'].

    Migracja z: SearchTestsNUXT/TestSearchListings.py — test_search_category_listing
    """
    listing = _open_listing(page, runtime_env, url)
    count = listing.content.content.count()
    assert count > 0, f"Listing '{url}' nie zawiera produktów."

    h1 = listing.get_h1_text()
    assert expected_h1_fragment.lower() in h1.lower(), (
        f"H1 '{h1}' nie zawiera oczekiwanego fragmentu "
        f"'{expected_h1_fragment}' dla URL '{url}'."
    )


@allure.feature("Wyszukiwanie — listingi kategorii (cache wyłączony)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("url,expected_h1_fragment", _CATEGORY_CASES)
@pytest.mark.scenario("Weryfikacja listingu kategorii przy wyłączonym cache HTML (?test=1)")
def test_search_category_listing_disabled_html_cache(page, runtime_env, url, expected_h1_fragment):
    """Tak samo jak test_search_category_listing, ale z parametrem ?test=1 wyłączającym cache.

    Migracja z: SearchTestsNUXT/TestSearchListings.py — test_search_category_listing_disabled_html_cache
    """
    listing = _open_listing(page, runtime_env, url + "?test=1")
    count = listing.content.content.count()
    assert count > 0, f"Listing '{url}?test=1' nie zawiera produktów."

    h1 = listing.get_h1_text()
    assert expected_h1_fragment.lower() in h1.lower(), (
        f"H1 '{h1}' nie zawiera oczekiwanego fragmentu "
        f"'{expected_h1_fragment}' dla URL '{url}?test=1'."
    )


# ---------------------------------------------------------------------------
# Producer listing tests
# ---------------------------------------------------------------------------

@allure.feature("Wyszukiwanie — listingi producentów")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("url,expected_producer", _PRODUCER_CASES)
@pytest.mark.scenario("Weryfikacja listingu producenta i nazwy w nagłówku H1")
def test_search_producer_listing(page, runtime_env, url, expected_producer):
    """Weryfikuje, że strona producenta zawiera produkty oraz że nagłówek H1
    zawiera oczekiwaną nazwę producenta.

    Migracja z: SearchTestsNUXT/TestSearchListings.py — test_search_producer_listing
    """
    listing = _open_listing(page, runtime_env, url)
    count = listing.content.content.count()
    assert count > 0, f"Listing producenta '{url}' nie zawiera produktów."

    h1 = listing.get_h1_text()
    assert expected_producer.lower() in h1.lower(), (
        f"H1 '{h1}' nie zawiera nazwy producenta '{expected_producer}' dla URL '{url}'."
    )


@allure.feature("Wyszukiwanie — listingi producentów (cache wyłączony)")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("url,expected_producer", _PRODUCER_CASES)
@pytest.mark.scenario("Weryfikacja listingu producenta przy wyłączonym cache HTML (?test=1)")
def test_search_producer_listing_disabled_html_cache(page, runtime_env, url, expected_producer):
    """Tak samo jak test_search_producer_listing, ale z parametrem ?test=1.

    Migracja z: SearchTestsNUXT/TestSearchListings.py — test_search_producer_listing_disabled_html_cache
    """
    listing = _open_listing(page, runtime_env, url + "?test=1")
    count = listing.content.content.count()
    assert count > 0, f"Listing producenta '{url}?test=1' nie zawiera produktów."

    h1 = listing.get_h1_text()
    assert expected_producer.lower() in h1.lower(), (
        f"H1 '{h1}' nie zawiera nazwy producenta '{expected_producer}' dla URL '{url}?test=1'."
    )
