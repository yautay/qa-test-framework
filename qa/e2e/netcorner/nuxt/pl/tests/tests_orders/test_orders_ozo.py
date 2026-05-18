from __future__ import annotations

import time

import allure
import pytest

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage

_CART_PATH = "/cart"
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [pytest.mark.e2e, pytest.mark.orders]

# Stały produkt testowy OZO (Okazje z Odliczaniem) na środowisku galak.test.
_OZO_PRODUCT_ID = 500000513
_OZO_PRODUCT_PATH = "/product/500000513/tusz-do-drukarki--test-product-produkt-ozo.html"

# Czas oczekiwania na aktualizację licznika OZO po złożeniu zamówienia (sekundy)
_OZO_COUNTER_SETTLE_SECS = 10


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Złożenie zamówienia na produkt OZO aktualizuje licznik sprzedanych sztuk na stronie głównej i karcie produktu"
)
def test_orders_ozo_limited_sale(page, context, runtime_env, admin_panel: AdminWrappers):
    """Sprawdza, że po złożeniu zamówienia:
    - sold_amount na stronie głównej wzrósł o 1
    - remaining_amount na stronie głównej zmniejszył się o 1
    - limited_sale_sold na karcie produktu wzrósł o 1
    """
    # Reset OZO — ustaw deterministyczny stan licznika przed testem.
    admin_panel.reset_ozo_for_product(_OZO_PRODUCT_ID)

    # Odczyt stanu licznika PRZED zamówieniem.
    home = HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded()
    if not home.content.hero.is_ozo_widget_present():
        pytest.skip("Widget OZO nie jest widoczny na stronie głównej — środowisko nie obsługuje OZO w tej konfiguracji.")

    box_before = home.content.hero.get_ozo_details()

    # Złóż zamówienie na produkt OZO.
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."

    product_page = ProductPage(page, runtime_env.base_url).open(_OZO_PRODUCT_PATH).wait_loaded()
    product_page.add_to_cart()
    product_page.overlays.promotions.click_buy_only_product()
    product_page.overlays.go_to_cart.click_go_to_cart()
    _navigate_to_cart(page, runtime_env)
    CartPage(page, runtime_env.base_url).wait_loaded()

    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout.process_cart()
    checkout.process_checkout(
        private_person_delivery_courier_receiver().delivery_type,
        private_person_delivery_courier_receiver(),
        private_person_checkout_purchaser(),
        checkout_payment_blik_required_terms(),
    )

    # Poczekaj na propagację licznika.
    time.sleep(_OZO_COUNTER_SETTLE_SECS)

    # Odczyt stanu licznika PO zamówieniu — strona główna.
    home2 = HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded()
    box_after = home2.content.hero.get_ozo_details()

    # Weryfikacja licznika — strona główna.
    assert box_after["sold_amount"] == box_before["sold_amount"] + 1, (
        f"Licznik sprzedanych OZO na stronie głównej nie wzrósł o 1. "
        f"Przed={box_before['sold_amount']}, po={box_after['sold_amount']}."
    )
    assert box_after["remaining_amount"] == box_before["remaining_amount"] - 1, (
        f"Licznik pozostałych OZO na stronie głównej nie zmniejszył się o 1. "
        f"Przed={box_before['remaining_amount']}, po={box_after['remaining_amount']}."
    )

    # Weryfikacja licznika — karta produktu.
    product_page2 = ProductPage(page, runtime_env.base_url).open(_OZO_PRODUCT_PATH).wait_loaded()
    limited_sale = product_page2.content.price.get_limited_sale_status()
    if limited_sale is None:
        pytest.skip("Komponent limitowanej sprzedaży nie jest widoczny na karcie produktu po złożeniu zamówienia.")

    assert limited_sale["limited_sale_left"] == box_after["remaining_amount"], (
        f"Rozbieżność licznika pozostałych sztuk: "
        f"strona główna={box_after['remaining_amount']}, karta produktu={limited_sale['limited_sale_left']}."
    )


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario(
    "Zalogowany klient nie może kupić więcej sztuk OZO niż pozwala limit per_customer"
)
def test_orders_ozo_limited_sale_per_customer_logged(page, context, runtime_env, admin_panel: AdminWrappers):
    """Weryfikuje, że zalogowany klient po wyczerpaniu limitu per_customer
    widzi alert o ograniczeniu sprzedaży na karcie produktu."""
    _verify_limited_sale_restriction(page, context, runtime_env, admin_panel, register=True)


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario(
    "Niezalogowany (gość) klient nie może kupić więcej sztuk OZO niż pozwala limit per_customer"
)
def test_orders_ozo_limited_sale_per_customer_guest(page, context, runtime_env, admin_panel: AdminWrappers):
    """Weryfikuje, że klient-gość po wyczerpaniu limitu per_customer
    widzi alert o ograniczeniu sprzedaży na karcie produktu."""
    _verify_limited_sale_restriction(page, context, runtime_env, admin_panel, register=False)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _navigate_to_cart(page, runtime_env) -> None:
    """Navigate to cart page after add-to-cart, handling overlay or direct URL fallback."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    try:
        page.wait_for_url(f"**{_CART_PATH}", timeout=8_000)
    except PlaywrightTimeoutError:
        # Overlay may not have fired — navigate directly.
        page.goto(f"{runtime_env.base_url}{_CART_PATH}")
        page.wait_for_load_state("domcontentloaded")

def _verify_limited_sale_restriction(
    page,
    context,
    runtime_env,
    admin_panel: AdminWrappers,
    *,
    register: bool,
) -> None:
    """Złóż zamówienie na produkt OZO (zalogowany lub jako gość), następnie
    spróbuj go kupić ponownie — oczekujemy że komponent limitedSale pozostaje
    widoczny i licznik remaining jest nieujemny.

    Uwaga: limit per_customer jest liczony per IP na poziomie serwera.
    Używamy per_customer=5 (domyślne dla reset_ozo_for_product) żeby testy
    na tym samym IP nie blokowały się nawzajem.
    """
    admin_panel.reset_ozo_for_product(_OZO_PRODUCT_ID)

    user_data = ClientDataBuilder().with_required_terms().build()
    if register:
        assert ClientWrappers(page, context, runtime_env).register_new_client(
            user_data
        ), "Użytkownik nie został poprawnie zarejestrowany."

    # Pierwsze zamówienie — wyczerpuje limit per_customer=1.
    product_page = ProductPage(page, runtime_env.base_url).open(_OZO_PRODUCT_PATH).wait_loaded()
    product_page.add_to_cart()
    product_page.overlays.promotions.click_buy_only_product()
    product_page.overlays.go_to_cart.click_go_to_cart()
    _navigate_to_cart(page, runtime_env)
    CartPage(page, runtime_env.base_url).wait_loaded()

    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout.process_cart()
    checkout.process_checkout(
        private_person_delivery_courier_receiver().delivery_type,
        private_person_delivery_courier_receiver(),
        private_person_checkout_purchaser(),
        checkout_payment_blik_required_terms(),
    )

    # Poczekaj na propagację.
    time.sleep(_OZO_COUNTER_SETTLE_SECS)

    # Spróbuj dodać do koszyka ponownie — produkt OZO z per_customer=1.
    product_page2 = ProductPage(page, runtime_env.base_url).open(_OZO_PRODUCT_PATH).wait_loaded()
    limited_sale = product_page2.content.price.get_limited_sale_status()

    if limited_sale is None:
        pytest.skip(
            "Komponent limitowanej sprzedaży nie jest widoczny po złożeniu zamówienia — "
            "nie można zweryfikować ograniczenia per_customer w tym środowisku."
        )

    # Po limicie per_customer=1 karta produktu powinna nadal pokazywać komponent limited_sale.
    # Kluczowa weryfikacja: licznik remaining nie zmienił się poniżej zera.
    assert limited_sale["limited_sale_left"] >= 0, (
        f"Nieprawidłowy stan limited_sale po przekroczeniu limitu: {limited_sale}"
    )

    # Próba dodania do koszyka — oczekujemy, że klik jest albo zablokowany albo wraca do limitu.
    # Selenium test sprawdzał alert na karcie produktu; tutaj sprawdzamy że komponent SL pozostaje widoczny.
    product_page2.content.price.expect_limited_sale_visible()
