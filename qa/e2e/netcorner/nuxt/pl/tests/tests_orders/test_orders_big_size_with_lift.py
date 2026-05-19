from __future__ import annotations

from decimal import Decimal

import allure
import pytest

from qa.e2e.netcorner.lib.price_utils import parse_price
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    DeliveryCourierReceiverDataBuilder,
    checkout_payment_prepaid_transfer_required_terms,
    private_person_checkout_purchaser,
)
from qa.e2e.netcorner.nuxt.pl.tests.helpers import add_products_to_cart_from_paths, open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_orders]

_PRODUCT_PATH = "/product/500000004/-test-product-produkt-g1.html"


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Produkt gabarytowy można zamówić z usługą wniesienia, gdy opcja jest dostępna")
def test_orders_big_size_with_lift(page, context, runtime_env, admin_panel):
    open_home_and_accept_cookies(page, runtime_env.base_url)
    add_products_to_cart_from_paths(page, runtime_env.base_url, [_PRODUCT_PATH])

    receiver = (
        DeliveryCourierReceiverDataBuilder()
        .with_lift_service()
        .build()
    )
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_prepaid_transfer_required_terms()

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    try:
        checkout_process_data = checkout_wrappers.process_checkout(
            receiver.delivery_type,
            receiver,
            purchaser,
            payment,
        )
    except RuntimeError as exc:
        if "wnies" in str(exc).casefold():
            pytest.skip("Środowisko testowe nie udostępnia obecnie aktywnej opcji wniesienia dla produktu G1.")
        raise

    order_number = checkout_process_data.typ_summary_data.order_number.strip()
    assert order_number, "Nie udało się potwierdzić złożenia zamówienia gabarytowego z wniesieniem."

    typ_total = parse_price(checkout_process_data.typ_summary_data.total_to_pay)
    assert typ_total is not None, "Nie udało się odczytać ceny końcowej na TYP dla dostawy z wniesieniem."
    admin_panel.assert_order_details(order_number, expected_summary_price=typ_total)


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Produkt gabarytowy bez wniesienia pozostaje scenariuszem referencyjnym")
def test_orders_big_size_without_lift(page, context, runtime_env, admin_panel):
    open_home_and_accept_cookies(page, runtime_env.base_url)
    add_products_to_cart_from_paths(page, runtime_env.base_url, [_PRODUCT_PATH])

    receiver = (
        DeliveryCourierReceiverDataBuilder()
        .build()
    )
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_prepaid_transfer_required_terms()

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_process_data = checkout_wrappers.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    order_number = checkout_process_data.typ_summary_data.order_number.strip()
    assert order_number, "Nie udało się potwierdzić złożenia zamówienia gabarytowego bez wniesienia."

    typ_total = parse_price(checkout_process_data.typ_summary_data.total_to_pay)
    assert typ_total is not None and typ_total >= Decimal("0"), (
        "Nie udało się odczytać poprawnej ceny końcowej na TYP dla dostawy gabarytowej bez wniesienia."
    )
    admin_panel.assert_order_details(order_number, expected_summary_price=typ_total)
