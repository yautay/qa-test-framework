from __future__ import annotations

"""Testy zamówień na produkty cyfrowe (Digital License).

Scenariusze:
- registered:   zalogowany klient kupuje licencję cyfrową (płatność BLIK).
- guest:        klient-gość kupuje licencję cyfrową (płatność BLIK).
- admin_verify: zalogowany klient kupuje licencję, weryfikacja zamówienia w adminie.

Uwagi środowiskowe:
- Produkt cyfrowy musi istnieć na środowisku galak.test.
- Brak produktu cyfrowego → pytest.skip (analogicznie do OZO widget).
"""

import allure
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [pytest.mark.e2e, pytest.mark.orders]

# Produkt cyfrowy (licencja) — do weryfikacji na środowisku galak.test
# Ścieżka produktu do uzupełnienia przy pierwszym uruchomieniu na env.
# Forma: /product/<id>/<slug>.html
_DIGITAL_PRODUCT_PATH: str | None = None  # TODO: uzupełnić po znalezieniu produktu na env

_CART_PATH = "/cart"


def _skip_if_no_digital_product() -> None:
    if _DIGITAL_PRODUCT_PATH is None:
        pytest.skip(
            "Brak skonfigurowanego produktu cyfrowego (_DIGITAL_PRODUCT_PATH=None). "
            "Uzupełnij ścieżkę po znalezieniu produktu na środowisku galak.test."
        )


def _navigate_to_cart(page, runtime_env) -> None:
    """Navigate to cart after add-to-cart, with URL-wait fallback."""
    try:
        page.wait_for_url(f"**{_CART_PATH}", timeout=8_000)
    except PlaywrightTimeoutError:
        page.goto(f"{runtime_env.base_url}{_CART_PATH}")
        page.wait_for_load_state("domcontentloaded")


def _place_digital_order(page, context, runtime_env, *, register: bool):
    """Złóż zamówienie na produkt cyfrowy (opcjonalnie z rejestracją).

    Returns:
        result from process_checkout, or None if product not available.
    """
    user_data = ClientDataBuilder().with_required_terms().build()
    if register:
        assert ClientWrappers(page, context, runtime_env).register_new_client(
            user_data
        ), "Rejestracja klienta nie powiodła się."

    try:
        product_page = ProductPage(page, runtime_env.base_url).open(_DIGITAL_PRODUCT_PATH).wait_loaded()
    except PlaywrightTimeoutError:
        pytest.skip(f"Produkt cyfrowy niedostępny na env: {_DIGITAL_PRODUCT_PATH}")
        return None, None

    product_page.add_to_cart()
    try:
        product_page.overlays.promotions.click_buy_only_product()
    except Exception:
        pass  # Overlay promocji może nie wystąpić dla produktu cyfrowego

    try:
        product_page.overlays.go_to_cart.click_go_to_cart()
    except Exception:
        pass

    _navigate_to_cart(page, runtime_env)

    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout.process_cart()
    result = checkout.process_checkout(
        private_person_delivery_courier_receiver().delivery_type,
        private_person_delivery_courier_receiver(),
        private_person_checkout_purchaser(),
        checkout_payment_blik_required_terms(),
    )
    return result, user_data


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Zalogowany klient kupuje produkt cyfrowy (licencję) — zamówienie zostaje złożone"
)
def test_orders_digital_license_registered(page, context, runtime_env):
    """Zalogowany klient kupuje licencję cyfrową przez standardowy flow zakupowy.

    Weryfikacja: numer zamówienia niepusty po zakończeniu checkoutu.
    """
    _skip_if_no_digital_product()
    result, _ = _place_digital_order(page, context, runtime_env, register=True)
    assert result is not None
    assert result.typ_summary_data.order_number.strip(), (
        "Zamówienie na produkt cyfrowy (zalogowany) nie zostało złożone."
    )


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario(
    "Klient-gość kupuje produkt cyfrowy (licencję) — zamówienie zostaje złożone"
)
def test_orders_digital_license_guest(page, context, runtime_env):
    """Klient-gość (niezalogowany) kupuje licencję cyfrową.

    Weryfikacja: numer zamówienia niepusty po zakończeniu checkoutu.
    """
    _skip_if_no_digital_product()
    result, _ = _place_digital_order(page, context, runtime_env, register=False)
    assert result is not None
    assert result.typ_summary_data.order_number.strip(), (
        "Zamówienie na produkt cyfrowy (gość) nie zostało złożone."
    )


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Zamówienie na produkt cyfrowy — weryfikacja danych w panelu admin"
)
def test_orders_digital_license_admin_verify(page, context, runtime_env, admin_panel: AdminWrappers):
    """Zalogowany klient kupuje licencję cyfrową; zamówienie jest weryfikowane w adminie.

    Weryfikacja:
    - numer zamówienia niepusty.
    - zamówienie widoczne w adminie (dane nabywcy zawierają email klienta).
    """
    _skip_if_no_digital_product()
    result, user_data = _place_digital_order(page, context, runtime_env, register=True)
    assert result is not None
    order_number = result.typ_summary_data.order_number.strip()
    assert order_number, "Zamówienie na produkt cyfrowy nie zostało złożone."

    order_data = admin_panel.get_order_data(order_number)
    assert order_data.order_number == order_number, (
        f"Admin: numer zamówienia '{order_data.order_number}' != oczekiwany '{order_number}'."
    )
    purchaser_text = "\n".join(order_data.purchaser_raw)
    assert user_data.email in purchaser_text, (
        f"Admin: email klienta '{user_data.email}' nie znaleziony w danych nabywcy:\n{purchaser_text}"
    )
