from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.product_opinion_component import ProductOpinionComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Na stronie produktu dostępny jest formularz dodawania opinii")
def test_add_product_opinion(page, runtime_env):
    listings_data = first_available_laptop_case()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()
    selected = listing.open_first_product_by_shipping_status(listings_data.product_availability_status)

    assert selected is not None, "Nie znaleziono produktu do przejścia na PDP."
    _, product_page = selected

    opinion = ProductOpinionComponent(product_page.page).wait_visible()
    assert opinion.has_required_fields(), "Formularz opinii nie zawiera kompletu wymaganych pól."
