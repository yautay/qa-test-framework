from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import CheckoutDeliveryCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import checkout_delivery_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import auth_session_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import AuthSessionCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_aviable_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.orders]


@allure.feature("Proces zakupowy")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda case: case.case_id)
@pytest.mark.parametrize("delivery_case", checkout_delivery_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Podstawowy proces zakupowy - typy dostawy")
def test_basic_orders(page, context, runtime_env, auth_case: AuthSessionCase, delivery_case: CheckoutDeliveryCase):
    _prepare_client_session(page, context, runtime_env, auth_case)
    selected_product_data = SelectProductWrappers(page, context, runtime_env).select_test_product(
        first_aviable_laptop_case()
    )
    assert selected_product_data is not None, "Nie udało się wybrać produktu testowego."
    assert selected_product_data.product_page_data is not None, "Produkt nie został dodany do koszyka."

    listing_data = selected_product_data.listing_data
    product_page_data = selected_product_data.product_page_data

    assert product_page_data.availability_status == listing_data.shipping_status, (
        f"Oczekiwany status dostępności produktu '{listing_data.shipping_status}' "
        f"różni się od tego wyświetlanego na stronie '{product_page_data.availability_status}'."
    )
    assert product_page_data.final_price == listing_data.final_price, (
        f"Oczekiwana cena produktu '{listing_data.final_price}' "
        f"różni się od tej wyświetlanej na stronie '{product_page_data.final_price}'."
    )
    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_wrappers.process_checkout(
        delivery_case.delivery_type,
        delivery_case.delivery_objects,
        delivery_case.purchaser_objects,
        delivery_case.payment_objects,
    )


def _prepare_client_session(page, context, runtime_env, auth_case: AuthSessionCase) -> bool:
    if not auth_case.authenticated:
        return False

    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Użytkownik nie został poprawnie zarejestrowany."
    )
    return True


