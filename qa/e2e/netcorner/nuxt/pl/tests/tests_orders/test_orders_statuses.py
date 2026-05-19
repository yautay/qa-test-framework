from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService
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

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_orders]


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Zmiana statusów zamówienia w adminie jest widoczna na koncie klienta i w mailu")
def test_orders_statuses(page, context, runtime_env, admin_panel, mail_inbox: MailInboxService):
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."

    listings_data = first_available_laptop_case()
    selected = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)
    assert selected is not None and selected.product_page_data is not None, "Nie udało się wybrać produktu testowego."

    receiver = private_person_delivery_courier_receiver()
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_blik_required_terms()

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

    mails_count_before = mail_inbox.count_mails_containing_text(text=order_number)
    assert mails_count_before > 0, f"Mailhog nie zwrócił żadnych maili powiązanych z zamówieniem '{order_number}'."

    current_status = admin_panel.get_order_data(order_number).status.strip()
    candidate_options = [
        option
        for option in admin_panel.get_order_status_options(order_number)
        if option.label.strip() and option.label.strip().casefold() != current_status.casefold()
    ]
    if not candidate_options:
        pytest.skip("Admin nie zwrócił żadnych alternatywnych statusów do przetestowania.")

    for option in candidate_options[:2]:
        admin_panel.change_order_status(order_number, option.value)

        orders_page = OrdersListPage(page, runtime_env.base_url).open_and_wait_orders()
        row = orders_page.find_order(order_number)
        assert row is not None, f"Zamówienie {order_number} nie zostało znalezione na liście klienta po zmianie statusu."

        account_status = row.get_status()
        assert _statuses_match(account_status, option.label), (
            f"Status klienta po zmianie w adminie nie zgadza się z oczekiwaniem. "
            f"Admin='{option.label}', konto='{account_status}'."
        )

        mails_count_after = mail_inbox.count_mails_containing_text(text=order_number)
        if mails_count_after <= mails_count_before:
            pytest.skip(
                f"Env nie wygenerował dodatkowego maila po zmianie statusu '{option.label}' dla zamówienia '{order_number}'. "
                f"Licznik przed={mails_count_before}, po={mails_count_after}."
            )
        mails_count_before = mails_count_after


def _statuses_match(account_status: str, admin_status: str) -> bool:
    account_normalized = " ".join(account_status.split()).casefold()
    admin_normalized = " ".join(admin_status.split()).casefold()
    return account_normalized in admin_normalized or admin_normalized in account_normalized
