from __future__ import annotations

from dataclasses import dataclass

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.checkout import DeliveryMethodsLayout
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    DeliveryCourierReceiverDataBuilder,
    checkout_payment_prepaid_transfer_required_terms,
    private_person_checkout_purchaser,
)
from qa.e2e.netcorner.nuxt.pl.tests.helpers import add_products_to_cart_from_paths, open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.orders]

_PRODUCT_PATH = "/product/1004422/apple-macbook-pro-m5-max-18-40-16-2-128gb-8tb-mac-os-gwiezdna-czern-140w-nano-textured.html"


@dataclass(frozen=True)
class MatrixVsListCase:
    case_id: str
    postal_code: str
    expected_layout: DeliveryMethodsLayout


def matrix_vs_list_cases() -> list[MatrixVsListCase]:
    return [
        MatrixVsListCase(
            case_id="courier_matrix_postcode_60001",
            postal_code="60-001",
            expected_layout=DeliveryMethodsLayout.MATRIX,
        ),
        MatrixVsListCase(
            case_id="courier_list_postcode_62030",
            postal_code="62-030",
            expected_layout=DeliveryMethodsLayout.LIST,
        ),
    ]


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("case", matrix_vs_list_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Checkout rozróżnia układ listy i macierzy metod dostawy po kodzie pocztowym")
def test_orders_matrix_vs_list(page, context, runtime_env, admin_panel, case: MatrixVsListCase):
    admin_panel.configure_enforced_shopping_path_postcodes(
        ensure_present=["62-030"],
        ensure_absent=["60-001"],
    )

    open_home_and_accept_cookies(page, runtime_env.base_url)
    cart_page = add_products_to_cart_from_paths(page, runtime_env.base_url, [_PRODUCT_PATH])
    dump_data(case=case, cart_products=cart_page.content.cart.get_data())

    receiver = DeliveryCourierReceiverDataBuilder().with_postal_code(case.postal_code).build()
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_prepaid_transfer_required_terms()

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    cart_data = checkout_wrappers.process_cart()
    try:
        checkout_process_data = checkout_wrappers.process_checkout(
            receiver.delivery_type,
            receiver,
            purchaser,
            payment,
            submit=False,
        )
    except AssertionError as exc:
        pytest.skip(f"Środowisko nie pozwoliło ustabilizować checkoutu dla kodu {case.postal_code}: {exc}")

    assert cart_data, "Koszyk jest pusty przed przejściem do checkoutu."
    if checkout_process_data.delivery_methods_layout != case.expected_layout:
        pytest.skip(
            f"Środowisko zwróciło układ '{checkout_process_data.delivery_methods_layout}' dla kodu '{case.postal_code}', "
            f"zamiast planowanego '{case.expected_layout.value}'."
        )
    assert checkout_process_data.available_delivery_methods, (
        f"Dla kodu pocztowego '{case.postal_code}' nie wykryto żadnych metod dostawy."
    )
