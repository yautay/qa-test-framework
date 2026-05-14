from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import auth_session_cases
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import AuthSessionCase
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listing_data_generators import first_available_laptop_case

pytestmark = [pytest.mark.e2e, pytest.mark.orders]


def _parse_price(price_text: str | None) -> Decimal | None:
    """Wyciąga pierwszą liczbę dziesiętną ze stringa ceny, np. '1 299,99 zł' → Decimal('1299.99')."""
    if price_text is None:
        return None
    normalized = re.sub(r"\s", "", price_text).replace(",", ".")
    match = re.search(r"\d+\.\d+|\d+", normalized)
    if not match:
        return None
    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda c: c.case_id)
@pytest.mark.scenario("Weryfikacja cen zamówienia w adminie")
def test_orders_prices(page, context, runtime_env, admin_panel, auth_case: AuthSessionCase):
    """Weryfikuje, że ceny wyświetlone na TYP zgadzają się z cenami w panelu admina.

    Scenariusz:
        1. Opcjonalna rejestracja klienta (zależnie od auth_case).
        2. Wybór produktu — odczyt ceny z listingu i strony produktu.
        3. Checkout (kurier + BLIK, nabywca prywatny).
        4. Potwierdzenie numeru zamówienia i ceny "Do zapłaty" na TYP.
        5. Weryfikacja sumy brutto w adminie — musi być >= ceny produktu brutto.
    """
    user_data = _prepare_client_session(page, context, runtime_env, auth_case)
    listings_data = first_available_laptop_case()

    selected_product_data = SelectProductWrappers(page, context, runtime_env).select_test_product(listings_data)
    assert selected_product_data is not None, "Nie udało się wybrać produktu testowego."
    assert selected_product_data.product_page_data is not None, "Produkt nie został dodany do koszyka."

    listing_price = _parse_price(listings_data.final_price)
    product_page_price = _parse_price(selected_product_data.product_page_data.final_price)

    receiver = private_person_delivery_courier_receiver()
    purchaser = private_person_checkout_purchaser()
    payment = checkout_payment_blik_required_terms()

    dump_data(
        auth_case=auth_case,
        listings_data=listings_data,
        user_data=user_data,
        product=selected_product_data.product,
        listing_price=listing_price,
        product_page_price=product_page_price,
    )

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_process_data = checkout_wrappers.process_checkout(
        receiver.delivery_type,
        receiver,
        purchaser,
        payment,
    )

    order_number = checkout_process_data.typ_summary_data.order_number.strip()
    assert order_number, "Nie udało się potwierdzić złożenia zamówienia: brak numeru zamówienia w podsumowaniu."

    typ_total = _parse_price(checkout_process_data.typ_summary_data.total_to_pay)
    assert typ_total is not None, (
        f"Nie udało się odczytać ceny 'Do zapłaty' na stronie TYP "
        f"(raw: '{checkout_process_data.typ_summary_data.total_to_pay}')."
    )

    # Cena produktu na listingu powinna równać się cenie na stronie produktu.
    if listing_price is not None and product_page_price is not None:
        assert listing_price == product_page_price, (
            f"Cena produktu na listingu '{listing_price}' różni się od ceny na stronie produktu "
            f"'{product_page_price}'."
        )

    # Suma brutto w adminie musi być >= ceny produktu (wlicza dostawę/płatność).
    admin_data = admin_panel.get_order_data(order_number)
    assert admin_data.summary_price_gross >= Decimal("0"), (
        f"Zamówienie {order_number}: nieprawidłowa cena brutto w adminie: '{admin_data.summary_price_gross}'."
    )

    if product_page_price is not None:
        assert admin_data.summary_price_gross >= product_page_price, (
            f"Zamówienie {order_number}: suma brutto w adminie '{admin_data.summary_price_gross}' "
            f"jest mniejsza niż cena produktu '{product_page_price}'. "
            f"Oczekiwano ceny >= {product_page_price} (produkty + dostawa)."
        )

    # Suma "Do zapłaty" na TYP musi zgadzać się z sumą brutto w adminie.
    assert typ_total == admin_data.summary_price_gross, (
        f"Zamówienie {order_number}: cena 'Do zapłaty' na TYP '{typ_total}' "
        f"różni się od sumy brutto w adminie '{admin_data.summary_price_gross}'."
    )


def _prepare_client_session(page, context, runtime_env, auth_case: AuthSessionCase):
    if not auth_case.authenticated:
        return None

    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."
    return user_data
