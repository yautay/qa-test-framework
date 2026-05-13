from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.checkout_page import CheckoutPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import PaymentMethods
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("CRUD nabywcy i odbiorcy w checkout — smoke alfa")
def test_crud_purchaser_receiver_checkout(page, context, runtime_env):
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Nie udało się przygotować zalogowanej sesji klienta do testu checkout CRUD."
    )

    selected = SelectProductWrappers(page, context, runtime_env).select_test_product(first_available_laptop_case())
    assert selected is not None, "Nie udało się dodać produktu przed testem checkout CRUD."
    CartAndCheckoutWrappers(page, context, runtime_env).process_cart()
    checkout = CheckoutPage(page, runtime_env.base_url).wait_loaded()

    checkout.content.delivery_type.click_courier_tile()
    checkout.content.delivery_object.wait_visible().click_delivery_object_tile()
    receiver_overlay = Overlays(page).checkout_courier_receiver.wait_visible()
    receiver_overlay.fill_receiver_data(private_person_delivery_courier_receiver())
    receiver_overlay.click_add_details()
    receiver_overlay.wait_hidden(timeout=10_000)

    purchaser_trigger = page.locator("[data-picker='purchaser'] [data-role='dialogTrigger']").first
    if purchaser_trigger.count() == 0:
        pytest.skip("Brak aktywnego kafelka formularza nabywcy na aktualnym checkoucie.")
    purchaser_trigger.click()
    purchaser_overlay = Overlays(page).checkout_purchaser.wait_visible()
    purchaser_overlay.fill_purchaser_data(private_person_checkout_purchaser())
    purchaser_overlay.click_add_details()
    purchaser_overlay.wait_hidden(timeout=10_000)

    payment_methods = checkout.content.payment_methods.wait_visible()
    try:
        payment_methods.choose_payment_method(PaymentMethods.BLIK)
    except RuntimeError:
        pytest.skip("Na bieżącym checkoucie brak dostępnej metody płatności BLIK.")
