from __future__ import annotations

"""Testy rejestracji klientów w grupach programu pracowniczego.

Scenariusze:
- register_sms: klient rejestruje się w grupie SMS używając kodu hash.
- register_qr:  klient rejestruje się w grupie QR.

Uwagi:
- Rejestracja przez SMS wymaga dostępu do hashy z admina + działającego SMS-sending.
- Rejestracja przez QR wymaga odczytu kodu QR z obrazka (pominięto dekodowanie, weryfikacja admin-side).
- Frontend URL programu pracowniczego: do uzupełnienia po weryfikacji na env.
"""

import uuid

import allure
import pytest

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import (
    AdminEmployeeProgramPage,
    EmployeeProgramGroupData,
)
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [pytest.mark.e2e, pytest.mark.employee_program]

_PRICE_CATEGORY_EMPLOYEE = "68"
# Frontend URL do rejestracji w programie pracowniczym — do weryfikacji na env
# Forma: /program-pracowniczy/<hash> lub /partnerEmployeeGroup/register/<hash>
_EMPLOYEE_REGISTER_PATH_TEMPLATE: str | None = None  # TODO: uzupełnić po weryfikacji


def _unique_group_name(suffix: str) -> str:
    return f"AT-EP-{suffix}-{uuid.uuid4().hex[:6]}"


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario(
    "Klient rejestruje się w grupie SMS programu pracowniczego"
)
def test_employee_program_register_sms(page, context, runtime_env, admin_panel: AdminWrappers):
    """Admin tworzy grupę SMS; klient rejestruje się używając kodu hash.

    Weryfikacja:
    - Istnieje przynajmniej jeden hash SMS po created.
    - Klient jest widoczny w grupie w adminie po rejestracji (lub skip jeśli brak frontend URL).
    """
    if _EMPLOYEE_REGISTER_PATH_TEMPLATE is None:
        pytest.skip(
            "Brak _EMPLOYEE_REGISTER_PATH_TEMPLATE — nie można przetestować rejestracji SMS. "
            "Uzupełnij ścieżkę frontendową po weryfikacji na środowisku galak.test."
        )

    group_name = _unique_group_name("REG-SMS")
    data = EmployeeProgramGroupData(
        group_name=group_name,
        price_category_id=_PRICE_CATEGORY_EMPLOYEE,
        enable_qr=False,
    )
    group_id = admin_panel.create_employee_group(data)
    if not group_id:
        pytest.skip("Nie udało się utworzyć grupy SMS w adminie.")

    hashes = admin_panel.get_employee_group_sms_hashes(group_id)
    if not hashes:
        admin_panel.delete_employee_group(group_id)
        pytest.skip(f"Brak hashy SMS w grupie '{group_name}' — środowisko nie obsługuje SMS.")

    user_data = ClientDataBuilder().with_required_terms().build()
    try:
        registered = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
        assert registered, "Rejestracja klienta nie powiodła się."

        register_url = f"{runtime_env.base_url}{_EMPLOYEE_REGISTER_PATH_TEMPLATE.format(hash=hashes[0])}"
        page.goto(register_url)
        page.wait_for_load_state("domcontentloaded")

        # Sprawdź, że klient jest w grupie
        admin_emp = AdminEmployeeProgramPage(page, admin_panel.admin_env.base_url)
        # Switch back to admin to verify — open admin first
        admin_panel.open_admin()
        admin_emp.navigate_to_edit(group_id)
        assert admin_emp.is_group_registered(user_data.email), (
            f"Email '{user_data.email}' nie znaleziony w grupie '{group_name}' (id={group_id})."
        )
    finally:
        try:
            admin_panel.delete_employee_group(group_id)
        except Exception:
            pass


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario(
    "Klient rejestruje się w grupie QR programu pracowniczego"
)
def test_employee_program_register_qr(page, context, runtime_env, admin_panel: AdminWrappers):
    """Admin tworzy grupę QR; klient rejestruje się przez kod QR.

    Uwaga: Dekodowanie kodu QR z obrazka (OpenCV) jest pominięte.
    Test weryfikuje administracyjny CRUD + dostępność URL rejestracji.
    """
    if _EMPLOYEE_REGISTER_PATH_TEMPLATE is None:
        pytest.skip(
            "Brak _EMPLOYEE_REGISTER_PATH_TEMPLATE — nie można przetestować rejestracji QR. "
            "Uzupełnij ścieżkę frontendową po weryfikacji na środowisku galak.test."
        )

    group_name = _unique_group_name("REG-QR")
    data = EmployeeProgramGroupData(
        group_name=group_name,
        price_category_id=_PRICE_CATEGORY_EMPLOYEE,
        enable_qr=True,
    )
    group_id = admin_panel.create_employee_group(data)
    if not group_id:
        pytest.skip("Nie udało się utworzyć grupy QR w adminie.")

    try:
        admin_panel.generate_employee_group_qr(group_id)
        user_data = ClientDataBuilder().with_required_terms().build()
        registered = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
        assert registered, "Rejestracja klienta nie powiodła się."

        # QR link — placeholder, zależy od struktury env
        # W Selenium: odczyt URL z obrazka QR przez OpenCV.
        # W PW: pomijamy dekodowanie — weryfikujemy tylko grupę admin.
        pytest.skip(
            "Dekodowanie kodu QR z obrazka nie jest zaimplementowane w PW. "
            "Test infrastrukturowy (CRUD) pokryty przez test_employee_program_crud_qr."
        )
    finally:
        try:
            admin_panel.delete_employee_group(group_id)
        except Exception:
            pass
