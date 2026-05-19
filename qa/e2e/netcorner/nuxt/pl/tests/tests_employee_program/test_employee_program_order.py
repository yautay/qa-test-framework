from __future__ import annotations

"""Testy zamówień z ceną pracowniczą (Employee Program — Order SMS/QR).

Scenariusze:
- order_sms: klient zarejestrowany w grupie SMS składa zamówienie z ceną pracowniczą.
- order_qr:  klient zarejestrowany w grupie QR składa zamówienie z ceną pracowniczą.

Wymagania:
- Klient musi być zarejestrowany w grupie programu pracowniczego.
- Frontend URL rejestracji musi być znany.
- Znany produkt z ceną pracowniczą.
"""

import uuid

import allure
import pytest

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import EmployeeProgramGroupData
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.tests.helpers import add_products_to_cart_from_paths

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_employee_program]

_PRICE_CATEGORY_EMPLOYEE = "68"

# TODO: uzupełnić po weryfikacji na środowisku — produkt z ceną pracowniczą
_EMPLOYEE_PRODUCT_PATH: str | None = None
# TODO: uzupełnić po weryfikacji na env — ścieżka rejestracji w grupie
_EMPLOYEE_REGISTER_PATH_TEMPLATE: str | None = None


def _unique_group_name(suffix: str) -> str:
    return f"AT-EP-{suffix}-{uuid.uuid4().hex[:6]}"


def _skip_if_not_configured() -> None:
    if _EMPLOYEE_PRODUCT_PATH is None or _EMPLOYEE_REGISTER_PATH_TEMPLATE is None:
        pytest.skip(
            "Brak konfiguracji produktu pracowniczego lub ścieżki rejestracji. "
            "Uzupełnij _EMPLOYEE_PRODUCT_PATH i _EMPLOYEE_REGISTER_PATH_TEMPLATE."
        )


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Klient z grupy SMS składa zamówienie z ceną pracowniczą"
)
def test_employee_program_order_sms(page, context, runtime_env, admin_panel: AdminWrappers):
    """Admin tworzy grupę SMS; klient rejestruje się → składa zamówienie; weryfikacja w adminie.

    Weryfikacja:
    - Zamówienie złożone (numer niepusty).
    - W adminie dane nabywcy zawierają email klienta.
    """
    _skip_if_not_configured()

    group_name = _unique_group_name("ORD-SMS")
    data = EmployeeProgramGroupData(
        group_name=group_name,
        price_category_id=_PRICE_CATEGORY_EMPLOYEE,
        enable_qr=False,
    )
    group_id = admin_panel.create_employee_group(data)
    if not group_id:
        pytest.skip("Nie udało się utworzyć grupy SMS.")

    hashes = admin_panel.get_employee_group_sms_hashes(group_id)
    if not hashes:
        admin_panel.delete_employee_group(group_id)
        pytest.skip("Brak hashy SMS w grupie — środowisko nie obsługuje SMS.")

    user_data = ClientDataBuilder().with_required_terms().build()
    order_number = ""
    try:
        registered = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
        assert registered, "Rejestracja klienta nie powiodła się."

        # Rejestracja w grupie przez hash
        register_url = f"{runtime_env.base_url}{_EMPLOYEE_REGISTER_PATH_TEMPLATE.format(hash=hashes[0])}"
        page.goto(register_url)
        page.wait_for_load_state("domcontentloaded")

        # Złóż zamówienie
        add_products_to_cart_from_paths(page, runtime_env.base_url, [_EMPLOYEE_PRODUCT_PATH])
        checkout = CartAndCheckoutWrappers(page, context, runtime_env)
        checkout.process_cart()
        result = checkout.process_checkout(
            private_person_delivery_courier_receiver().delivery_type,
            private_person_delivery_courier_receiver(),
            private_person_checkout_purchaser(),
            checkout_payment_blik_required_terms(),
        )
        order_number = result.typ_summary_data.order_number.strip()
        assert order_number, "Zamówienie SMS (pracownicze) nie zostało złożone."

        # Weryfikacja w adminie
        order_data = admin_panel.get_order_data(order_number)
        purchaser_text = "\n".join(order_data.purchaser_raw)
        assert user_data.email in purchaser_text, (
            f"Admin: email '{user_data.email}' nie znaleziony w zamówieniu '{order_number}'."
        )
    finally:
        try:
            admin_panel.delete_employee_group(group_id)
        except Exception:
            pass


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Klient z grupy QR składa zamówienie z ceną pracowniczą"
)
def test_employee_program_order_qr(page, context, runtime_env, admin_panel: AdminWrappers):
    """Admin tworzy grupę QR; klient rejestruje się przez QR → składa zamówienie; weryfikacja w adminie.

    Uwaga: Dekodowanie kodu QR z obrazka jest pominięte.
    Test jest zaznaczony jako skip do czasu implementacji QR decode na PW.
    """
    _skip_if_not_configured()

    group_name = _unique_group_name("ORD-QR")
    data = EmployeeProgramGroupData(
        group_name=group_name,
        price_category_id=_PRICE_CATEGORY_EMPLOYEE,
        enable_qr=True,
    )
    group_id = admin_panel.create_employee_group(data)
    if not group_id:
        pytest.skip("Nie udało się utworzyć grupy QR.")

    try:
        admin_panel.generate_employee_group_qr(group_id)
        pytest.skip(
            "Dekodowanie kodu QR z obrazka nie jest zaimplementowane w PW. "
            "Rejestracja QR wymaga odczytu URL z obrazka QR (w Selenium: OpenCV). "
            "Pomiń ten test do czasu dodania biblioteki QR decode."
        )
    finally:
        try:
            admin_panel.delete_employee_group(group_id)
        except Exception:
            pass
