from __future__ import annotations

import uuid

import allure
import pytest
from playwright.sync_api import expect

from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_prepaid_transfer_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.tests.helpers import accept_cookie_banner_if_visible, open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.orders]

_PROMO_CODE = "TECHAGGREGATORBRUTTO"


@allure.feature("Agregator")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Produkt z agregatora pozwala przejść do koszyka z kodem promocyjnym")
def test_aggregator_promo_code(page, context, runtime_env, admin_panel):
    suffix = uuid.uuid4().hex[:8]
    frontend_url = admin_panel.create_products_aggregator(
        name=f"Agregator promo {suffix}",
        work_name=f"Agregator promo {suffix}",
        url_slug=f"agregator-promo-{suffix}",
        item_name="Klawiatury promo",
        section_code="Agregator",
        product_codes="KL-LOG-094",
        discount_code=_PROMO_CODE,
    )

    open_home_and_accept_cookies(page, runtime_env.base_url)
    page.goto(frontend_url, wait_until="domcontentloaded")
    accept_cookie_banner_if_visible(page)

    expect(page.locator("[data-name='aggregatorSlider']")).to_be_visible(timeout=15_000)
    page.get_by_role("button", name="Sprawdź").first.click()
    page.wait_for_load_state("domcontentloaded")
    accept_cookie_banner_if_visible(page)

    page.get_by_role("button", name="Dodaj do koszyka").first.click()
    page.wait_for_load_state("domcontentloaded")
    accept_cookie_banner_if_visible(page)
    page.goto(page.url, wait_until="domcontentloaded")
    accept_cookie_banner_if_visible(page)
    product_page = ProductPage(page, runtime_env.base_url).wait_loaded()
    product_page.add_to_cart()
    page.goto(f"{runtime_env.base_url}/cart", wait_until="domcontentloaded")
    cart_page = CartPage(page, runtime_env.base_url).wait_loaded()

    cart_page.content.summary.enter_coupon_code(_PROMO_CODE)
    cart_page.content.summary.click_add_coupon_code()
    expect(page.locator("#couponCode")).to_have_value(_PROMO_CODE, timeout=10_000)

    receiver = private_person_delivery_courier_receiver()
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

    assert checkout_process_data.typ_summary_data.order_number.strip(), (
        "Nie udało się złożyć zamówienia z produktem pochodzącym z agregatora promo."
    )
