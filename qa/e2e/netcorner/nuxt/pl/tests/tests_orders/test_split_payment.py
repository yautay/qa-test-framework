from __future__ import annotations

from dataclasses import dataclass

import allure
import pytest

from qa.e2e.netcorner.lib.price_utils import parse_price
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    CheckoutPaymentDataBuilder,
    DeliveryStorehouseReceiverDataBuilder,
    company_checkout_purchaser,
    company_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.tests.helpers import add_products_to_cart_from_paths, open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_orders]

_PRODUCT_PATH = "/product/1004422/apple-macbook-pro-m5-max-18-40-16-2-128gb-8tb-mac-os-gwiezdna-czern-140w-nano-textured.html"


@dataclass(frozen=True)
class SplitPaymentCase:
    case_id: str
    delivery_factory: object


def split_payment_cases() -> list[SplitPaymentCase]:
    return [
        SplitPaymentCase(
            case_id="courier_split_payment",
            delivery_factory=company_delivery_courier_receiver,
        ),
        SplitPaymentCase(
            case_id="store_pickup_split_payment",
            delivery_factory=lambda: DeliveryStorehouseReceiverDataBuilder().with_storehouse_name("Outlet Komorniki").build(),
        ),
    ]


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("case", split_payment_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Split payment pozostaje dostępny dla drogich produktów")
def test_split_payment(page, context, runtime_env, admin_panel, case: SplitPaymentCase):
    open_home_and_accept_cookies(page, runtime_env.base_url)
    cart_page = add_products_to_cart_from_paths(page, runtime_env.base_url, [_PRODUCT_PATH])
    cart_summary = cart_page.content.summary.get_data()
    assert parse_price(cart_summary.products_value_gross) is not None, "Nie udało się odczytać wartości koszyka."

    receiver = case.delivery_factory()
    purchaser = company_checkout_purchaser()
    payment = CheckoutPaymentDataBuilder().with_payment_method_label_contains("splitpayment").with_required_terms().build()

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_process_data = checkout_wrappers.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    assert any("splitpayment" in method.name.replace(" ", "").casefold() for method in checkout_process_data.available_payment_methods), (
        f"Dla przypadku '{case.case_id}' nie wykryto metody Split Payment na checkoutcie."
    )
    order_number = checkout_process_data.typ_summary_data.order_number.strip()
    assert order_number, f"Nie udało się złożyć zamówienia split payment dla przypadku '{case.case_id}'."

    typ_total = parse_price(checkout_process_data.typ_summary_data.total_to_pay)
    assert typ_total is not None, f"Nie udało się odczytać ceny TYP dla przypadku '{case.case_id}'."
    admin_panel.assert_order_details(order_number, expected_summary_price=typ_total)
