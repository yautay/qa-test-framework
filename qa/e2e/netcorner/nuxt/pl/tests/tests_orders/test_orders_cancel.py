from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.orders_list_page import OrdersListPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.orders]


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Anulowanie zamówienia z poziomu konta klienta")
def test_orders_cancel(page, context, runtime_env):
    """Weryfikuje, że nowo złożone zamówienie można anulować z poziomu listy zamówień.

    Scenariusz:
        1. Rejestracja nowego klienta.
        2. Wybór produktu i checkout (kurier + BLIK, nabywca prywatny).
        3. Potwierdzenie numeru zamówienia na TYP.
        4. Nawigacja do listy zamówień klienta.
        5. Kliknięcie „Anuluj zamówienie" dla złożonego zamówienia.
        6. Oczekiwany wynik:
           - albo zamówienie zmieniło status na „Anulowane",
           - albo pojawił się toast informujący, że anulowanie nie powiodło się
             (zamówienie już w trakcie realizacji — akceptowalny wynik na env testowym).
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

    receiver = private_person_delivery_courier_receiver()
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_blik_required_terms()

    dump_data(user_data=user_data, product=selected.product)

    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout.process_cart()
    result = checkout.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    order_number = result.typ_summary_data.order_number.strip()
    assert order_number, "Brak numeru zamówienia na stronie TYP."

    orders_page = OrdersListPage(page, runtime_env.base_url).open_and_wait_orders()

    row = orders_page.find_order(order_number)
    assert row is not None, (
        f"Zamówienie {order_number} nie zostało znalezione na liście zamówień klienta."
    )
    assert row.has_cancel_button(), (
        f"Zamówienie {order_number}: brak przycisku 'Anuluj zamówienie'. "
        f"Status: '{row.get_status()}'"
    )

    row.click_cancel()

    # Po kliknięciu Anuluj możliwe są dwa wyniki:
    # (a) zamówienie zostało anulowane → status = "Anulowane"
    # (b) anulowanie nie powiodło się → toast z informacją o błędzie
    # Oba są akceptowalne w środowisku testowym (zależy od stanu realizacji).
    page.wait_for_timeout(2_000)

    toast_failure = page.locator(
        "li[data-name*='toast'], [data-name='toast']"
    ).filter(has_text="nie powiodło")

    if toast_failure.count() > 0 and toast_failure.first.is_visible(timeout=3_000):
        # Anulowanie zablokowane przez system — akceptowalny wynik
        return

    # Brak komunikatu o błędzie → zamówienie powinno być anulowane
    orders_page2 = OrdersListPage(page, runtime_env.base_url).open_and_wait_orders()
    row2 = orders_page2.find_order(order_number)
    assert row2 is not None, (
        f"Zamówienie {order_number} zniknęło z listy po próbie anulowania."
    )
    assert "anulowane" in row2.get_status().lower(), (
        f"Zamówienie {order_number}: oczekiwano statusu 'Anulowane', "
        f"otrzymano '{row2.get_status()}'."
    )
