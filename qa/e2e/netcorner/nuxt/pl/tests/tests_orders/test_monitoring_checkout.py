from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import CheckoutDeliveryCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import checkout_delivery_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.orders]


@allure.feature("Monitoring — dostępność checkout")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("delivery_case", checkout_delivery_cases(), ids=lambda c: c.case_id)
@pytest.mark.scenario("Monitoring checkout — pełen przepływ bez składania zamówienia")
def test_monitoring_checkout(page, context, runtime_env, delivery_case: CheckoutDeliveryCase):
    """Weryfikuje, że cały przepływ checkout jest dostępny bez finalnego złożenia zamówienia.

    Scenariusz:
        1. Rejestracja nowego klienta (pełna sesja).
        2. Wybór produktu z listingu.
        3. Przejście koszyk → checkout z daną kombinacją dostawy i płatności.
        4. Asercja, że przycisk „Zamawiam z obowiązkiem zapłaty" jest widoczny
           (wszystkie kroki zostały pomyślnie wypełnione).
        5. Zamówienie NIE jest składane.

    Pokrycie: 8 kombinacji (4 typy dostawy × 2 typy nabywcy).
    """
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."

    listings_data = first_available_laptop_case()
    selected = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)
    assert selected is not None and selected.product_page_data is not None, (
        "Nie udało się wybrać produktu testowego."
    )

    dump_data(delivery_case=delivery_case, user_data=user_data, product=selected.product)

    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout.process_cart()
    result = checkout.process_checkout(
        delivery_case.delivery_type,
        delivery_case.delivery_objects,
        delivery_case.purchaser_objects,
        delivery_case.payment_objects,
        submit=False,
    )

    assert result.summary_data.total_to_pay, (
        f"Wariant {delivery_case.case_id}: brak kwoty 'Do zapłaty' w podsumowaniu — "
        "checkout mógł nie dotrzeć do ostatniego kroku."
    )
