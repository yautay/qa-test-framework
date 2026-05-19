from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_orders]

# Stałe produkty testowe z minimalną ilością zamówieniową na środowisku galak.test.
# 500000510 = "ZESTAW PRODUKTOWY"        — min_qty=3
# 500000511 = "ZESTAW PRODUKTOWY + CENA JEDN." — min_qty=2
_MIN_QTY_PRODUCTS = [
    pytest.param(
        "/product/500000510/tusz-do-drukarki--test-product-zestaw-produktowy.html",
        "min_qty_product_1",
        id="min_qty_product_1",
    ),
    pytest.param(
        "/product/500000511/tusz-do-drukarki--test-product-zestaw-produktowy-cena-jednostkowa.html",
        "min_qty_product_w_unit_price",
        id="min_qty_product_w_unit_price",
    ),
]


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Zamówienie produktu z minimalną ilością zamówieniową")
@pytest.mark.parametrize("path,label", _MIN_QTY_PRODUCTS, ids=lambda p: p if isinstance(p, str) else None)
def test_orders_min_qty(page, context, runtime_env, path, label):
    """Weryfikuje, że produkt z min_qty zostaje dodany do koszyka w wymaganej ilości.

    Scenariusz:
        1. Rejestracja nowego klienta.
        2. Otwarcie karty produktu — odczyt atrybutu ``data-min-qty``.
        3. Dodanie produktu do koszyka.
        4. Weryfikacja, że ilość w koszyku == min_qty z karty produktu.
        5. Checkout (kurier + BLIK) i potwierdzenie numeru zamówienia na TYP.
    """
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."

    product_page = ProductPage(page, runtime_env.base_url).open(path).wait_loaded()
    min_qty = product_page.content.price.get_min_qty()

    assert min_qty is not None and 1 < min_qty < 100, (
        f"Produkt {label}: nieprawidłowa wartość min_qty={min_qty}. "
        f"Oczekiwano wartości w zakresie 2–99. "
        f"Upewnij się, że produkt ma zdefiniowaną minimalną ilość zamówieniową."
    )

    dump_data(label=label, path=path, min_qty=min_qty)

    product_page.add_to_cart()

    cart_page = CartPage(page, runtime_env.base_url).open(CartPage.PATH).wait_loaded()
    cart_data = cart_page.content.cart.get_data()

    # Sprawdź ilość produktu w koszyku — powinna równać się min_qty z karty produktu.
    # Produkt jest identyfikowany przez ID wyciągnięte z URL ścieżki.
    cart_items = list(cart_data.values())
    assert len(cart_items) > 0, "Koszyk jest pusty po dodaniu produktu."

    cart_qty = cart_items[0].quantity
    assert cart_qty == min_qty, (
        f"Produkt {label}: oczekiwano ilości {min_qty} (min_qty), "
        f"a w koszyku jest {cart_qty}."
    )

    # Kontynuuj przez checkout — weryfikacja numeru zamówienia na TYP.
    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    receiver = private_person_delivery_courier_receiver()
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_blik_required_terms()

    cart_page.proceed_to_checkout()
    result = checkout.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    order_number = result.typ_summary_data.order_number.strip()
    assert order_number, (
        f"Produkt {label}: zamówienie zostało złożone, ale brak numeru zamówienia na TYP."
    )
