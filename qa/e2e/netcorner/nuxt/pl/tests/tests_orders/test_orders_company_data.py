from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    company_checkout_purchaser,
    company_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import auth_session_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import AuthSessionCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.orders]

_COMPANY_NIP = "7770020640"


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda c: c.case_id)
@pytest.mark.scenario("Zamówienie z danymi firmowymi (NIP)")
def test_orders_company_data(page, context, runtime_env, admin_panel, auth_case: AuthSessionCase):
    """Weryfikuje, że zamówienie złożone z danymi firmowymi zawiera poprawny NIP w panelu admina.

    Scenariusz:
        1. Opcjonalna rejestracja klienta (zależnie od auth_case).
        2. Wybór produktu i przejście przez checkout z nabywcą firmowym (kurier + BLIK).
        3. Potwierdzenie numeru zamówienia na stronie TYP.
        4. Weryfikacja NIP nabywcy w panelu admina.
    """
    user_data = _prepare_client_session(page, context, runtime_env, auth_case)
    listings_data = first_available_laptop_case()

    selected_product_data = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)
    assert selected_product_data is not None, "Nie udało się wybrać produktu testowego."
    assert selected_product_data.product_page_data is not None, "Produkt nie został dodany do koszyka."

    purchaser = company_checkout_purchaser()
    receiver = company_delivery_courier_receiver()
    payment = checkout_payment_blik_required_terms()

    dump_data(
        auth_case=auth_case,
        listings_data=listings_data,
        user_data=user_data,
        product=selected_product_data.product,
        purchaser=purchaser,
    )

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_process_data = checkout_wrappers.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    order_number = checkout_process_data.typ_summary_data.order_number.strip()
    assert order_number, "Nie udało się potwierdzić złożenia zamówienia: brak numeru zamówienia w podsumowaniu."

    # Weryfikacja NIP w adminie — nazwa firmy pochodzi z GUS (nie z buildera),
    # więc asercja opiera się wyłącznie na numerze NIP.
    admin_panel.assert_order_details(
        order_number,
        expected_nip=_COMPANY_NIP,
    )


def _prepare_client_session(page, context, runtime_env, auth_case: AuthSessionCase):
    if not auth_case.authenticated:
        return None

    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."
    return user_data
