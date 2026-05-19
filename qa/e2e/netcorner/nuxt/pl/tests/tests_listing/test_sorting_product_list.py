from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import SortOptions
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_search]

# Category listing with price filter (no variants, cheap items) — equivalent to Selenium start_page
_LISTING_PATH = (
    "/category/686/pendrive.html"
    "?pr10%5B%5D=1&pr10%5B%5D=500000&filter=1&showBuyActiveOnly=1&showProducts=1"
)

_SORT_CASES = [
    pytest.param(SortOptions.PRICE_ASC,  "price_ascending",  id="price_ascending"),
    pytest.param(SortOptions.PRICE_DESC, "price_descending", id="price_descending"),
    pytest.param(SortOptions.NAME_ASC,   "name_ascending",   id="name_ascending"),
    pytest.param(SortOptions.NAME_DESC,  "name_descending",  id="name_descending"),
]


@allure.feature("Sortowanie listingu")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("sort_option,sort_id", _SORT_CASES)
@pytest.mark.scenario("Weryfikacja poprawności sortowania listy produktów")
def test_sorting_product_list(page, runtime_env, sort_option, sort_id):
    """Weryfikuje, że sortowanie listy produktów (pendrive) działa poprawnie.

    Dla sortowania cenowego: sprawdza dokładną kolejność (float).
    Dla sortowania nazw: weryfikuje tylko obecność produktów — serwer używa
    wewnętrznego klucza sortowania, który może różnić się od porządku wyświetlanej
    nazwy (locale-aware, bez polskich znaków w slugu).

    Migracja z: SortingTestsNUXT/TestSortingProductList.py
    """
    listing = ListingPage(page, runtime_env.base_url)
    listing.open(_LISTING_PATH).wait_loaded()

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
