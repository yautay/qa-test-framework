from __future__ import annotations

import pytest

from qa.e2e.netcorner.nuxt.pl.app.data.orders import ORDER_SMOKE_CASES
from qa.e2e.netcorner.nuxt.pl.app.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.app.pages.checkout_page import CheckoutPage
from qa.scenario import scenario

pytestmark = [pytest.mark.e2e, pytest.mark.smoke]


def _run_orders_case(page, context, runtime_env, case):
    if not runtime_env.base_url:
        pytest.skip("BASE_URL not set")

    # Context isolation guard: each parametrized case must start in a fresh context.
    assert context.cookies() == []

    if case["channel"] in {"delivery", "mixed"}:
        checkout_page = CheckoutPage(page, runtime_env.base_url)
        checkout_page.open()
        assert checkout_page.is_ready(), f"Navigation failed for scenario {case['id']}"
    else:
        cart_page = CartPage(page, runtime_env.base_url)
        cart_page.open()
        assert cart_page.is_ready(), f"Navigation failed for scenario {case['id']}"


DELIVERY_CASES = [case for case in ORDER_SMOKE_CASES if case["legacy_group"] == "test_order_delivery"]
PICKUP_CASES = [case for case in ORDER_SMOKE_CASES if case["legacy_group"] == "test_order_pickup"]
DIGITAL_CASES = [case for case in ORDER_SMOKE_CASES if case["legacy_group"] == "test_order_digital"]
MIXED_CASES = [case for case in ORDER_SMOKE_CASES if case["legacy_group"] == "test_order_mixed"]


@pytest.mark.parametrize("case", DELIVERY_CASES, ids=[case["id"] for case in DELIVERY_CASES])
@scenario("Smoke: scenariusz dostawy do domu przechodzi do etapu checkout")
def test_order_delivery(page, context, runtime_env, case):
    _run_orders_case(page, context, runtime_env, case)
    checkout_page = CheckoutPage(page, runtime_env.base_url)
    assert (
        checkout_page.has_interactive_checkout_surface()
    ), f"Checkout form surface not detected for scenario {case['id']}"


@pytest.mark.parametrize("case", PICKUP_CASES, ids=[case["id"] for case in PICKUP_CASES])
@scenario("Smoke: scenariusz odbioru własnego przechodzi przez koszyk")
def test_order_pickup(page, context, runtime_env, case):
    _run_orders_case(page, context, runtime_env, case)
    cart_page = CartPage(page, runtime_env.base_url)
    assert cart_page.has_interactive_cart_surface(), f"Cart interactive surface not detected for scenario {case['id']}"


@pytest.mark.parametrize("case", DIGITAL_CASES, ids=[case["id"] for case in DIGITAL_CASES])
@scenario("Smoke: scenariusz produktu cyfrowego przechodzi startowy flow")
def test_order_digital(page, context, runtime_env, case):
    _run_orders_case(page, context, runtime_env, case)


@pytest.mark.parametrize("case", MIXED_CASES, ids=[case["id"] for case in MIXED_CASES])
@scenario("Smoke: scenariusz mieszany (cyfrowy + fizyczny) przechodzi startowy flow")
def test_order_mixed(page, context, runtime_env, case):
    _run_orders_case(page, context, runtime_env, case)
