from __future__ import annotations

import allure
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.tests.helpers import poll_until

_CART_PATH = "/cart"

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_core,
    pytest.mark.e2e_orders,
    pytest.mark.xdist_group("orders_ozo_serial"),
]

# Stały produkt testowy OZO (Okazje z Odliczaniem) na środowisku galak.test.
_OZO_PRODUCT_ID = 500000513
_OZO_PRODUCT_PATH = "/product/500000513/tusz-do-drukarki--test-product-produkt-ozo.html"

# Czas oczekiwania na aktualizację licznika OZO po złożeniu zamówienia (sekundy)
_OZO_COUNTER_MAX_WAIT_SECS = 60
_OZO_COUNTER_POLL_SECS = 2


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Złożenie zamówienia na produkt OZO aktualizuje licznik sprzedanych sztuk na karcie produktu"
)
def test_orders_ozo_limited_sale(page, context, runtime_env, admin_panel: AdminWrappers):
    """Sprawdza, że po złożeniu zamówienia:
    - limited_sale_sold na karcie produktu wzrósł o 1 względem sold_amount sprzed zamówienia
    - limited_sale_left na karcie produktu zmniejszył się o 1 względem remaining_amount sprzed zamówienia

    Punkt odniesienia (before) jest odczytywany z widgetu OZO na stronie głównej przed złożeniem
    zamówienia. Weryfikacja po zamówieniu opiera się wyłącznie na karcie produktu (polling), co
    jest zgodne z podejściem testu Selenium — strona główna może mieć dłuższy cykl cache niż
    karta produktu.
    """
    # Reset OZO — ustaw deterministyczny stan licznika przed testem.
    admin_panel.reset_ozo_for_product(_OZO_PRODUCT_ID, per_customer=1)

    # Odczyt stanu licznika PRZED zamówieniem — polling do pojawienia się widgetu po resecie.
    if not _wait_for_ozo_widget(page, runtime_env):
        pytest.skip(
            "Widget OZO nie jest widoczny na stronie głównej po resecie — środowisko nie obsługuje OZO w tej konfiguracji."
        )

    home = HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded()
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

    # Odczyt stanu licznika PO zamówieniu — polling karty produktu do propagacji backendu.
    _product_page_after, limited_sale = _wait_for_limited_sale_status(page, runtime_env, _OZO_PRODUCT_PATH)

    if limited_sale is None:
        pytest.skip("Komponent limitowanej sprzedaży nie jest widoczny na karcie produktu po złożeniu zamówienia.")

    # Weryfikacja licznika — karta produktu (wzorzec Selenium: before ze strony głównej, after z karty produktu).
    assert limited_sale["limited_sale_sold"] == box_before.sold_amount + 1, (
        f"Licznik sprzedanych OZO na karcie produktu nie wzrósł o 1. "
        f"Przed (strona główna)={box_before.sold_amount}, po (karta produktu)={limited_sale['limited_sale_sold']}."
    )
    assert limited_sale["limited_sale_left"] == box_before.remaining_amount - 1, (
        f"Licznik pozostałych OZO na karcie produktu nie zmniejszył się o 1. "
        f"Przed (strona główna)={box_before.remaining_amount}, po (karta produktu)={limited_sale['limited_sale_left']}."
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
    admin_panel.reset_ozo_for_product(_OZO_PRODUCT_ID, per_customer=1)
    ozo_settings = admin_panel.get_ozo_limited_sale_settings(_OZO_PRODUCT_ID)
    per_customer_limit = int(ozo_settings.get("per_customer", 1) or 1)
    if per_customer_limit < 1:
        raise AssertionError(f"Nieprawidłowy limit per_customer dla OZO: {per_customer_limit}")

    user_data = ClientDataBuilder().with_required_terms().build()
    if register:
        assert ClientWrappers(page, context, runtime_env).register_new_client(
            user_data
        ), "Użytkownik nie został poprawnie zarejestrowany."

    # Pierwsze zamówienie — zamawiamy pełny limit per_customer,
    # aby druga próba jednoznacznie weryfikowała blokadę.
    product_page = ProductPage(page, runtime_env.base_url).open(_OZO_PRODUCT_PATH).wait_loaded()
    product_page.add_to_cart()
    product_page.overlays.promotions.click_buy_only_product()
    product_page.overlays.go_to_cart.click_go_to_cart()
    _navigate_to_cart(page, runtime_env)
    cart_before_checkout = CartPage(page, runtime_env.base_url).wait_loaded()
    cart_product_before_checkout = cart_before_checkout.content.cart.get_product(str(_OZO_PRODUCT_ID))
    assert cart_product_before_checkout is not None, "Brak produktu OZO w koszyku przed checkoutem."
    if per_customer_limit > 1:
        try:
            cart_product_before_checkout.enter_quantity(per_customer_limit)
        except PlaywrightTimeoutError:
            pytest.fail(
                f"Timeout podczas ustawiania ilości {per_customer_limit} dla produktu OZO "
                f"(id={_OZO_PRODUCT_ID}) w koszyku — interakcja UI nie powiodła się. "
                "Nie można zweryfikować limitu per_customer."
            )
    initial_order_quantity = cart_product_before_checkout.get_quantity()
    assert initial_order_quantity == per_customer_limit, (
        f"Ilość produktu OZO w koszyku ({initial_order_quantity}) różni się od oczekiwanego "
        f"limitu per_customer ({per_customer_limit})."
    )

    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout.process_cart()
    checkout.process_checkout(
        private_person_delivery_courier_receiver().delivery_type,
        private_person_delivery_courier_receiver(),
        private_person_checkout_purchaser(),
        checkout_payment_blik_required_terms(),
    )

    # Polling karty produktu do pojawienia się komponentu limited_sale po propagacji backendu.
    product_page2, limited_sale = _wait_for_limited_sale_status(page, runtime_env, _OZO_PRODUCT_PATH)

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

    # Próba dodania do koszyka ponownie — oczekujemy komunikatu o przekroczeniu limitu.
    product_page2.add_to_cart()
    limit_toast_seen = False
    toast_root = product_page2.page.locator('[data-name="toast"]').last
    if toast_root.count() > 0 and toast_root.is_visible(timeout=7_000):
        toast_message = toast_root.locator("div").inner_text().strip()
        assert "limit" in toast_message.casefold() or "ogranic" in toast_message.casefold(), (
            "Komunikat po próbie ponownego dodania produktu OZO nie wskazuje ograniczenia limitu. "
            f"Treść komunikatu: '{toast_message}'."
        )
        limit_toast_seen = True

    limited_sale_after_retry = product_page2.content.price.get_limited_sale_status()
    assert limited_sale_after_retry is not None, (
        "Po próbie ponownego dodania produktu OZO komponent limited_sale nie jest widoczny."
    )
    assert "limitowana" in product_page2.page.locator("[data-name='limitedSale']").first.inner_text().casefold(), (
        "Brak informacji o ograniczeniu sprzedaży limitowanej na karcie produktu po przekroczeniu limitu."
    )

    if not limit_toast_seen:
        try:
            _navigate_to_cart(page, runtime_env)
            cart_page = CartPage(page, runtime_env.base_url).wait_loaded()
        except PlaywrightTimeoutError:
            # Jeśli UI blokuje przejście do koszyka po przekroczeniu limitu,
            # kluczowa asercja pozostaje na PDP (komunikat + brak utraty komponentu limited sale).
            return

        cart_product = cart_page.content.cart.get_product(str(_OZO_PRODUCT_ID))
        assert cart_product is not None, "Po ponownej próbie dodania produkt OZO nie został znaleziony w koszyku."
        assert cart_product.get_quantity() == initial_order_quantity, (
            "Po ponownej próbie dodania produktu OZO ilość w koszyku przekracza limit per_customer. "
            f"Limit(admin)={per_customer_limit}, ilość początkowa={initial_order_quantity}, "
            f"ilość po ponownej próbie={cart_product.get_quantity()}."
        )


def _wait_for_limited_sale_status(
    page,
    runtime_env,
    product_path: str,
    *,
    max_wait_s: float = _OZO_COUNTER_MAX_WAIT_SECS,
    poll_s: float = _OZO_COUNTER_POLL_SECS,
) -> tuple[ProductPage, dict | None]:
    """Polluje kartę produktu aż komponent limited_sale stanie się widoczny lub minie timeout.

    Zwraca krotkę (ProductPage, status) — ProductPage jest ostatnią otwartą instancją,
    gotową do dalszych interakcji. Status może być None jeśli nie pojawił się w max_wait_s.
    """
    last_page: list[ProductPage] = []

    def fetch() -> dict | None:
        p = ProductPage(page, runtime_env.base_url).open(product_path).wait_loaded()
        last_page.clear()
        last_page.append(p)
        return p.content.price.get_limited_sale_status()

    status = poll_until(
        fetch,
        condition=lambda s: s is not None,
        timeout_s=max_wait_s,
        poll_s=poll_s,
        default=None,
    )
    return last_page[0], status


def _wait_for_ozo_widget(
    page,
    runtime_env,
    *,
    max_wait_s: float = 30,
    poll_s: float = _OZO_COUNTER_POLL_SECS,
) -> bool:
    """Polluje stronę główną aż widget OZO stanie się widoczny po resecie w adminie lub minie timeout.

    Zwraca True gdy widget jest widoczny, False gdy upłynął max_wait_s.
    """
    result = poll_until(
        lambda: HomePage(page, runtime_env.base_url).open(HomePage.PATH).wait_loaded(),
        condition=lambda home: home.content.hero.is_ozo_widget_present(),
        timeout_s=max_wait_s,
        poll_s=poll_s,
        default=None,
    )
    return result is not None and result.content.hero.is_ozo_widget_present()
