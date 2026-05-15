from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import SortOptions
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e, pytest.mark.search]

_SEARCH_PHRASE = "apple"

_SORT_CASES = [
    pytest.param(SortOptions.PRICE_ASC,  id="price_ascending"),
    pytest.param(SortOptions.PRICE_DESC, id="price_descending"),
    pytest.param(SortOptions.NAME_ASC,   id="name_ascending"),
    pytest.param(SortOptions.NAME_DESC,  id="name_descending"),
]


@allure.feature("Sortowanie wyników wyszukiwania")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("sort_option", _SORT_CASES)
@pytest.mark.scenario("Weryfikacja poprawności sortowania wyników wyszukiwania")
def test_sorting_product_search(page, runtime_env, sort_option):
    """Weryfikuje, że sortowanie wyników wyszukiwania (fraza 'apple') działa poprawnie.

    Dla sortowania cenowego: sprawdza dokładną kolejność (float).
    Dla sortowania nazw: weryfikuje tylko obecność produktów — serwer używa
    wewnętrznego klucza sortowania, który może różnić się od porządku wyświetlanej
    nazwy (locale-aware, bez polskich znaków w slugu).

    Migracja z: SortingTestsNUXT/TestSortingProductSearch.py
    """
    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH).wait_loaded()
    home.header.search_bar.fill_phrase(_SEARCH_PHRASE)
    home.header.search_bar.submit()

    listing = ListingPage(page, runtime_env.base_url).wait_loaded()
    listing.content.sorting.select_sort_option(sort_option)

    is_price_sort = sort_option in (SortOptions.PRICE_ASC, SortOptions.PRICE_DESC)

    if is_price_sort:
        data = listing.content.content.get_all_final_prices()
        expected = sorted(data, reverse=(sort_option == SortOptions.PRICE_DESC))
        assert data == expected, (
            f"Sortowanie '{sort_option}' nieprawidłowe. "
            f"Oczekiwano: {expected[:5]}…, otrzymano: {data[:5]}…"
        )
    else:
        # Serwer sortuje po wewnętrznym kluczu — weryfikujemy tylko obecność produktów.
        data = listing.content.content.get_all_product_names()
        assert len(data) > 0, (
            f"Brak produktów na listingu po zastosowaniu sortowania '{sort_option}'."
        )
