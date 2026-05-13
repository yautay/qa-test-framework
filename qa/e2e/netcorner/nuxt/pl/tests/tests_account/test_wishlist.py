from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_aviable_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.scenario("Dodawanie produktu do listy życzeń")
def test_add_product_to_wishlist(page, context, runtime_env):
    user_data = ClientDataBuilder().with_required_terms().build()
    dump_data(user_data=user_data)
    ClientWrappers(page, context, runtime_env).register_new_client(user_data)
    listings_data = first_aviable_laptop_case()
    selected_product_data = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data, add_to_cart=False)
    assert selected_product_data is not None, "Nie udało się otworzyć karty produktu."
    product_page = ProductPage(page, runtime_env.base_url)
    product_page.click_wishlist()
    product_page.overlays.wishlist.click_create_new_list()
    product_page.overlays.wishlist.enter_wishlist_name("Testowa lista życzeń")
    product_page.overlays.wishlist.click_create_wishlist()
    

