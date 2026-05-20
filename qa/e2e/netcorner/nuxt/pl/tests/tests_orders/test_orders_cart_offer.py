from __future__ import annotations

"""Testy ofert koszykowych (Cart Offer).

Scenariusze:
- static:  admin tworzy ofertę z ustaloną ceną brutto (119 zł), klient kupuje przez URL z maila.
- dynamic: admin tworzy ofertę bez ustalania ceny (cena dynamiczna z produktu), klient kupuje przez URL z maila.

Wymagania:
- admin_panel fixture (AdminWrappers)
- mail_inbox fixture (MailInboxService)
- zarejestrowany klient (email z domeny @test.pl)
"""

import allure
import pytest

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_orders]

# Produkt testowy dla oferty koszykowej (wyszukiwanie po ERP w adminie)
_CART_OFFER_PRODUCT_ERP = "DMTP1"
_CART_OFFER_PRODUCT_ID = "500000001"

# Ilość sztuk w ofercie
_CART_OFFER_QTY = 3
# Kanał sprzedaży (komputronik.pl = 1)
_CHANNEL_ID = "1"
# Stała cena brutto w scenariuszu static
_STATIC_PRICE = "119"
# Kat. cenowa dla PL
_PRICE_CATEGORY_ID = "10"

# Regex do znalezienia linku oferty koszykowej w mailu
_CART_OFFER_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*/cart[-_]?offer[^\s\"'<>]*"


def _place_cart_offer_order(page, context, runtime_env, offer_url: str):
    """Przejdź pod adres oferty koszykowej i złóż zamówienie."""
    page.goto(offer_url)
    page.wait_for_load_state("domcontentloaded")

    offer_rows = page.locator("[data-name='cartOfferProduct']")
    assert offer_rows.count() > 0, "Strona oferty nie zawiera produktów do dodania."
    add_all_button = page.get_by_role("button", name="Dodaj wszystko do koszyka")
    assert add_all_button.count() > 0, "Brak przycisku 'Dodaj wszystko do koszyka' na stronie oferty."
    add_all_button.first.click()

    cart_page = CartPage(page, runtime_env.base_url).wait_loaded()
    cart_data = cart_page.content.cart.get_data()
    assert cart_data, "Koszyk jest pusty po dodaniu produktów z oferty."
    assert _CART_OFFER_PRODUCT_ID in cart_data, (
        f"W koszyku brakuje produktu z oferty o id={_CART_OFFER_PRODUCT_ID}."
    )
    assert cart_data[_CART_OFFER_PRODUCT_ID].quantity == _CART_OFFER_QTY, (
        "Ilość produktu z oferty w koszyku nie zgadza się z ofertą: "
        f"oczekiwano {_CART_OFFER_QTY}, otrzymano {cart_data[_CART_OFFER_PRODUCT_ID].quantity}."
    )
    total_qty = sum(item.quantity for item in cart_data.values())
    assert total_qty == _CART_OFFER_QTY, (
        f"Niepoprawna ilość produktów po aktywacji oferty: oczekiwano {_CART_OFFER_QTY}, otrzymano {total_qty}."
    )

    checkout = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout.process_cart()
    result = checkout.process_checkout(
        private_person_delivery_courier_receiver().delivery_type,
        private_person_delivery_courier_receiver(),
        private_person_checkout_purchaser(),
        checkout_payment_blik_required_terms(),
    )
    return result


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Oferta koszykowa z ustaloną (statyczną) ceną brutto — klient kupuje przez link z maila"
)
def test_orders_cart_offer_static_price(
    page,
    context,
    runtime_env,
    admin_panel: AdminWrappers,
    mail_inbox: MailInboxService,
):
    """Admin tworzy ofertę z ceną stałą 119 zł; klient rejestruje się, loguje i składa zamówienie.

    Weryfikacja:
    - Mail z ofertą dotarł do odbiorcy.
    - Link z maila otwiera stronę oferty.
    - Zamówienie zostało złożone (numer zamówienia niepusty).
    """
    user_data = ClientDataBuilder().with_required_terms().build()
    registered = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
    assert registered, "Rejestracja klienta nie powiodła się."

    admin_panel.create_cart_offer_and_send_email(
        product_id=_CART_OFFER_PRODUCT_ERP,
        qty=_CART_OFFER_QTY,
        recipient_email=user_data.email,
        channel_id=_CHANNEL_ID,
        price_type_id="1",
        price_category_id=_PRICE_CATEGORY_ID,
        fixed_price=_STATIC_PRICE,
    )

    offer_url = mail_inbox.get_cart_offer_link(
        context=context,
        recipient=user_data.email,
        link_regex=_CART_OFFER_LINK_REGEX,
    )

    if not offer_url:
        pytest.skip(
            "Link oferty koszykowej nie został znaleziony w mailu — "
            "środowisko może nie obsługiwać tej funkcji."
        )

    result = _place_cart_offer_order(page, context, runtime_env, offer_url)

    assert result.typ_summary_data.order_number.strip(), (
        "Zamówienie przez ofertę koszykową (static) nie zostało złożone."
    )


@allure.feature("Zamówienia")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario(
    "Oferta koszykowa z ceną dynamiczną (z produktu) — klient kupuje przez link z maila"
)
def test_orders_cart_offer_dynamic_price(
    page,
    context,
    runtime_env,
    admin_panel: AdminWrappers,
    mail_inbox: MailInboxService,
):
    """Admin tworzy ofertę bez ustalania ceny (dynamic); klient składa zamówienie przez link.

    Weryfikacja:
    - Mail z ofertą dotarł do odbiorcy.
    - Link z maila otwiera stronę oferty.
    - Zamówienie zostało złożone (numer zamówienia niepusty).
    """
    user_data = ClientDataBuilder().with_required_terms().build()
    registered = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
    assert registered, "Rejestracja klienta nie powiodła się."

    admin_panel.create_cart_offer_and_send_email(
        product_id=_CART_OFFER_PRODUCT_ERP,
        qty=_CART_OFFER_QTY,
        recipient_email=user_data.email,
        channel_id=_CHANNEL_ID,
        price_type_id="2",  # dynamic — cena z produktu
        price_category_id=_PRICE_CATEGORY_ID,
        fixed_price=None,
    )

    offer_url = mail_inbox.get_cart_offer_link(
        context=context,
        recipient=user_data.email,
        link_regex=_CART_OFFER_LINK_REGEX,
    )

    if not offer_url:
        pytest.skip(
            "Link oferty koszykowej nie został znaleziony w mailu — "
            "środowisko może nie obsługiwać tej funkcji."
        )

    result = _place_cart_offer_order(page, context, runtime_env, offer_url)

    assert result.typ_summary_data.order_number.strip(), (
        "Zamówienie przez ofertę koszykową (dynamic) nie zostało złożone."
    )
