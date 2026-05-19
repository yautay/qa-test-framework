from __future__ import annotations

from dataclasses import dataclass

import allure
import pytest

from qa.e2e.netcorner.lib.price_utils import parse_price
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    DeliveryCourierReceiverDataBuilder,
    DeliveryStorehouseReceiverDataBuilder,
    checkout_payment_blik_required_terms,
    checkout_payment_cash_on_pickup_required_terms,
    private_person_checkout_purchaser,
)
from qa.e2e.netcorner.nuxt.pl.tests.helpers import add_products_to_cart_from_paths, open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_orders]


@dataclass(frozen=True)
class DimensionModuleCase:
    case_id: str
    product_paths: list[str]
    delivery_factory: object
    payment_factory: object


def dimension_module_cases() -> list[DimensionModuleCase]:
    return [
        DimensionModuleCase(
            case_id="gn_courier",
            product_paths=["/product/500000001/-test-product-produkt-gn.html"],
            delivery_factory=lambda: DeliveryCourierReceiverDataBuilder().build(),
            payment_factory=checkout_payment_blik_required_terms,
        ),
        DimensionModuleCase(
            case_id="g6_inpost",
            product_paths=["/product/500000002/-test-product-produkt-g6.html"],
            delivery_factory=lambda: DeliveryStorehouseReceiverDataBuilder()
            .with_storehouse_name("Outlet Komorniki")
            .build(),
            payment_factory=checkout_payment_blik_required_terms,
        ),
        DimensionModuleCase(
            case_id="g1w_store_pickup",
            product_paths=["/product/500000003/-test-product-produkt-g1w.html"],
            delivery_factory=lambda: DeliveryStorehouseReceiverDataBuilder()
            .with_storehouse_name("Outlet Komorniki")
            .build(),
            payment_factory=checkout_payment_cash_on_pickup_required_terms,
        ),
    ]


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("case", dimension_module_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Scenariusze modułu gabarytów pozwalają przejść checkout dla wspieranych kombinacji")
def test_orders_dimension_module(page, context, runtime_env, admin_panel, case: DimensionModuleCase):
    open_home_and_accept_cookies(page, runtime_env.base_url)
    cart_page = add_products_to_cart_from_paths(page, runtime_env.base_url, case.product_paths)
    cart_data = cart_page.content.cart.get_data()
    assert len(cart_data) == len(case.product_paths), (
        f"Oczekiwano {len(case.product_paths)} pozycji w koszyku, znaleziono {len(cart_data)}."
    )

    receiver = case.delivery_factory()
    purchaser = private_person_checkout_purchaser()
    payment = case.payment_factory()

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_process_data = checkout_wrappers.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    order_number = checkout_process_data.typ_summary_data.order_number.strip()
    assert order_number, f"Nie udało się złożyć zamówienia dla przypadku '{case.case_id}'."

    typ_total = parse_price(checkout_process_data.typ_summary_data.total_to_pay)
    assert typ_total is not None, f"Nie udało się odczytać ceny końcowej dla przypadku '{case.case_id}'."
    admin_panel.assert_order_details(order_number, expected_summary_price=typ_total)
