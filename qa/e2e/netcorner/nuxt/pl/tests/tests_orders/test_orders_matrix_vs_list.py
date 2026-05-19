from __future__ import annotations

from dataclasses import dataclass

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.checkout import DeliveryMethodsLayout
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    DeliveryCourierReceiverDataBuilder,
    checkout_payment_prepaid_transfer_required_terms,
    private_person_checkout_purchaser,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listings_data_models import ListingsData
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import AvailabilityStatuses
from qa.e2e.netcorner.nuxt.pl.tests.helpers import open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.orders]

_CATEGORY_URL = "category/2954/myszki-komputerowe.html"


@dataclass(frozen=True)
class MatrixVsListCase:
    case_id: str
    postal_code: str
    city: str
    expected_layout: DeliveryMethodsLayout | None


def matrix_vs_list_cases() -> list[MatrixVsListCase]:
    return [
        MatrixVsListCase(
            case_id="courier_checkout_baseline_postcode_60001",
            postal_code="60-001",
            city="Poznań",
            expected_layout=DeliveryMethodsLayout.MATRIX,
        ),
        MatrixVsListCase(
            case_id="courier_list_postcode_62030",
            postal_code="62-030",
            city="Luboń",
            expected_layout=DeliveryMethodsLayout.LIST,
        ),
    ]


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("case", matrix_vs_list_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Checkout respektuje wymuszoną listę metod dostawy i zachowuje działający baseline dla innych kodów")
def test_orders_matrix_vs_list(page, context, runtime_env, admin_panel, case: MatrixVsListCase):
    admin_panel.configure_enforced_shopping_path_postcodes(
        ensure_present=["62-030"],
        ensure_absent=["60-001"],
    )

    open_home_and_accept_cookies(page, runtime_env.base_url)
    listings_data = ListingsData(
        category_url=_CATEGORY_URL,
        product_availability_status=AvailabilityStatuses.ONE_DAY,
    )
    selected_product_data = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)
    assert selected_product_data is not None, "Nie udało się wybrać produktu z kategorii myszek komputerowych."
    assert selected_product_data.product_page_data is not None, "Produkt nie został dodany do koszyka."
    dump_data(case=case, listing=selected_product_data.listing_data, product=selected_product_data.product)

    receiver = DeliveryCourierReceiverDataBuilder().with_postal_code(case.postal_code).with_city(case.city).build()
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_prepaid_transfer_required_terms()

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    cart_data = checkout_wrappers.process_cart()
    checkout_process_data = checkout_wrappers.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
        submit=False,
    )

    assert cart_data, "Koszyk jest pusty przed przejściem do checkoutu."
    if case.expected_layout is not None and checkout_process_data.delivery_methods_layout != case.expected_layout:
        actual_layout = checkout_process_data.delivery_methods_layout
        actual_label = actual_layout.value if actual_layout else "unknown"
        assert actual_layout == case.expected_layout, (
            f"Kod '{case.postal_code}' zwrócił układ '{actual_label}', "
            f"oczekiwano '{case.expected_layout.value}'."
        )
    assert checkout_process_data.available_delivery_methods, (
        f"Dla kodu pocztowego '{case.postal_code}' nie wykryto żadnych metod dostawy."
    )
