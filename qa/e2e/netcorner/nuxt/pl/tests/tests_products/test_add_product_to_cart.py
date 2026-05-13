from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import phase2_listing_cases

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("listing_case", phase2_listing_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Dodanie produktu do koszyka z listingu")
def test_add_product_to_cart(page, context, runtime_env, listing_case):
    listings_data = listing_case.factory()
    selected = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)

    assert selected is not None, "Nie udało się wybrać produktu testowego z listingu."
    assert selected.product is not None, "Nie udało się odczytać danych produktu z karty produktu."

    cart = CartPage(page, runtime_env.base_url).wait_loaded()
    cart_data = cart.content.cart.get_data()
    dump_data(listing_case=listing_case, selected_product=selected.product, cart_product_ids=list(cart_data.keys()))

    assert cart_data, "Koszyk jest pusty po dodaniu produktu."
    product_names = [item.product_name for item in cart_data.values()]
    expected_name = selected.product.product_name.strip()
    assert any(expected_name and expected_name in name for name in product_names), (
        f"Nie znaleziono produktu '{expected_name}' w koszyku."
    )
