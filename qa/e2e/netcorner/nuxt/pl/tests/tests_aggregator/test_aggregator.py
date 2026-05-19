from __future__ import annotations

import uuid

import allure
import pytest
from playwright.sync_api import expect

from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.tests.helpers import accept_cookie_banner_if_visible, open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_orders]


@allure.feature("Agregator")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Agregator produktowy utworzony w adminie prowadzi do pełnego checkoutu")
def test_aggregator(page, context, runtime_env, admin_panel):
    suffix = uuid.uuid4().hex[:8]
    frontend_url = admin_panel.create_products_aggregator(
        name=f"Agregator produkty {suffix}",
        work_name=f"Agregator produkty {suffix}",
        url_slug=f"agregator-products-{suffix}",
        item_name="Klawiatury",
        section_code="Agregator",
        product_codes="KL-NAT-038,KL-LOG-094,LT-STD-I15-DEL-1300",
    )

    open_home_and_accept_cookies(page, runtime_env.base_url)
    page.goto(frontend_url, wait_until="domcontentloaded")
    accept_cookie_banner_if_visible(page)

    expect(page.locator("[data-name='aggregatorSlider']")).to_be_visible(timeout=15_000)
    assert page.locator("[data-name='cardProduct']").count() > 0, (
        "Agregator nie wyświetlił żadnych produktów na froncie."
    )

    page.get_by_role("button", name="Sprawdź").first.click()
    page.wait_for_load_state("domcontentloaded")
    accept_cookie_banner_if_visible(page)

    product_page = ProductPage(page, runtime_env.base_url).wait_loaded()
    product_page.add_to_cart()
    product_page.overlays.promotions.click_buy_only_product()
    product_page.overlays.go_to_cart.click_go_to_cart()

    receiver = private_person_delivery_courier_receiver()
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_blik_required_terms()

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_process_data = checkout_wrappers.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    assert checkout_process_data.typ_summary_data.order_number.strip(), (
        "Nie udało się potwierdzić złożenia zamówienia z produktu pochodzącego z agregatora."
    )
