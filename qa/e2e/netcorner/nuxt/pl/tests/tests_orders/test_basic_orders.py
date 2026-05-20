from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.overlays import Overlays
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import CheckoutDeliveryCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import checkout_delivery_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import AuthSessionCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import (
    ClientDataBuilder,
    auth_session_cases_basic_orders,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_orders]


@allure.feature("Proces zakupowy")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize("auth_case", auth_session_cases_basic_orders(), ids=lambda case: case.case_id)
@pytest.mark.parametrize("delivery_case", checkout_delivery_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Podstawowy proces zakupowy - typy dostawy")
def test_basic_orders(page, context, runtime_env, auth_case: AuthSessionCase, delivery_case: CheckoutDeliveryCase):
    page.goto(runtime_env.base_url, wait_until="domcontentloaded")
    if runtime_env.server_name == "prod":
        context.add_cookies([{"name": "recaptcha_test", "value": "on", "url": runtime_env.base_url}])
        page.reload(wait_until="domcontentloaded")
    user_data = _prepare_client_session(page, context, runtime_env, auth_case)
    listings_data = first_available_laptop_case()
    selected_product_data = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)
    assert selected_product_data is not None, "Nie udało się wybrać produktu testowego."
    assert selected_product_data.product_page_data is not None, "Produkt nie został dodany do koszyka."

    dump_data(
        auth_case=auth_case,
        delivery_case=delivery_case,
        listings_data=listings_data,
        user_data=user_data,
        product=selected_product_data.product,
    )

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
    checkout_wrappers.process_cart(continue_without_login=not auth_case.login_in_cart_overlay)
    if auth_case.login_in_cart_overlay:
        assert user_data is not None, "Brak danych zarejestrowanego klienta do logowania w koszyku."
        Overlays(page).login.wait_visible().log_client(user_data.email, user_data.password)

    checkout_process_data = checkout_wrappers.process_checkout(
        delivery_case.delivery_type,
        delivery_case.delivery_objects,
        delivery_case.purchaser_objects,
        delivery_case.payment_objects,
    )
    assert checkout_process_data.typ_summary_data.order_number.strip(), (
        "Nie udało się potwierdzić złożenia zamówienia: brak numeru zamówienia w podsumowaniu."
    )


def _prepare_client_session(page, context, runtime_env, auth_case: AuthSessionCase):
    if not auth_case.authenticated and not auth_case.register_before_flow:
        return None

    user_data = ClientDataBuilder().with_required_terms().build()
    client_wrappers = ClientWrappers(page, context, runtime_env)
    assert client_wrappers.register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."
    if auth_case.register_before_flow and not auth_case.authenticated:
        client_wrappers.logout_client()
    return user_data
