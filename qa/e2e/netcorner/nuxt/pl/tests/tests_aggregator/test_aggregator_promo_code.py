from __future__ import annotations

import uuid
from urllib.parse import urlparse

import allure
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.tests.helpers import (
    accept_cookie_banner_if_visible,
    add_products_to_cart_from_paths,
    open_home_and_accept_cookies,
)

pytestmark = [pytest.mark.e2e, pytest.mark.orders]

_PROMO_CODE = "TECHAGGREGATORBRUTTO"


def _aggregator_product_paths(page) -> list[str]:
    cards = page.locator("[data-name='cardProduct']")
    paths: list[str] = []
    for index in range(cards.count()):
        href = cards.nth(index).locator("a[href*='/product/']").first.get_attribute("href")
        if not href:
            continue
        parsed = urlparse(href)
        if parsed.path and parsed.path not in paths:
            paths.append(parsed.path)
    return paths


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
        product_codes="KL-NAT-038,KL-LOG-094,LT-STD-I15-DEL-1300",
        discount_code=_PROMO_CODE,
    )

    open_home_and_accept_cookies(page, runtime_env.base_url)
    page.goto(frontend_url, wait_until="domcontentloaded")
    accept_cookie_banner_if_visible(page)

    expect(page.locator("[data-name='aggregatorSlider']")).to_be_visible(timeout=15_000)
    product_paths = _aggregator_product_paths(page)
    assert product_paths, "Agregator promo nie zwrócił żadnych linków produktowych."

    cart_page = None
    last_error: Exception | None = None
    for product_path in product_paths[:3]:
        try:
            cart_page = add_products_to_cart_from_paths(page, runtime_env.base_url, [product_path])
            if cart_page.content.cart.get_data():
                break
        except PlaywrightTimeoutError as exc:
            last_error = exc
            page.goto(frontend_url, wait_until="domcontentloaded")
            accept_cookie_banner_if_visible(page)

    assert cart_page is not None and cart_page.content.cart.get_data(), (
        "Nie udało się dodać produktu z agregatora promo do koszyka. "
        f"Ostatni błąd: {last_error}"
    )

    cart_page.content.summary.enter_coupon_code(_PROMO_CODE)
    cart_page.content.summary.click_add_coupon_code()
    expect(page.locator("#couponCode")).to_have_value(_PROMO_CODE, timeout=10_000)

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
        "Nie udało się złożyć zamówienia z produktem pochodzącym z agregatora promo."
    )
