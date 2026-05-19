from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core]

# Kategoria z produktami — pełny zakres bez filtra "tylko dostępne",
# żeby po włączeniu checkboxa tymczasowo niedostępne były widoczne.
_LAPTOPS_LISTING_URL = "search-filter/5022/laptopy-do-gier"


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Na listingu można wyświetlić produkty tymczasowo niedostępne")
def test_temporarily_unavailable_products(page, runtime_env):
    listing = ListingPage(page, f"{runtime_env.base_url}/{_LAPTOPS_LISTING_URL}").open().wait_loaded()

    # Włącz widoczność niedostępnych produktów
    listing.content.sorting.set_show_unavailable(True)
    listing.content.content.wait_for_tiles()

    tiles = page.locator("[data-name='listingTile']")
    total = tiles.count()
    assert total > 0, "Brak jakichkolwiek kafelków po włączeniu widoczności niedostępnych produktów."

    # Produkt niedostępny nie ma widocznego przycisku "Dodaj do koszyka"
    unavailable_count = 0
    for i in range(total):
        add_btn = tiles.nth(i).locator("[data-name='addToCartButton']").first
        if add_btn.count() == 0 or not add_btn.is_visible():
            unavailable_count += 1

    assert unavailable_count > 0, (
        f"Nie wykryto produktów niedostępnych spośród {total} kafelków na listingu "
        f"(oczekiwano przynajmniej jednego bez przycisku 'Dodaj do koszyka')."
    )
