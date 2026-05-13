from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import phase2_listing_cases

pytestmark = [pytest.mark.e2e]


@allure.feature("Produkty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("listing_case", phase2_listing_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Status dostępności produktu na listingu i PDP jest spójny")
def test_product_availability(page, runtime_env, listing_case):
    listings_data = listing_case.factory()
    listing = ListingPage(page, f"{runtime_env.base_url}/{listings_data.category_url}").open().wait_loaded()
    selected = listing.open_first_product_by_shipping_status(listings_data.product_availability_status)

    assert selected is not None, (
        f"Nie znaleziono produktu o statusie '{listings_data.product_availability_status.status}'."
    )

    listing_product_data, product_page = selected
    product_price_data = product_page.content.price.get_data()
    dump_data(listing_case=listing_case, listing_data=listing_product_data, product_data=product_price_data)

    assert product_price_data.availability_status == listing_product_data.shipping_status, (
        "Status dostępności na stronie produktu różni się od statusu na listingu. "
        f"Listing: '{listing_product_data.shipping_status}', PDP: '{product_price_data.availability_status}'."
    )
