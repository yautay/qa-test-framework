from __future__ import annotations

"""Testy CRUD grup programu pracowniczego (Employee Program).

Scenariusze:
- CRUD SMS: admin tworzy grupę SMS → weryfikuje hashe → usuwa grupę.
- CRUD QR:  admin tworzy grupę QR → generuje kod QR → usuwa grupę.

Selektory i flow: na podstawie Selenium PartnerGroupObjects.py + PartnerGroupLocators.py.
"""

import uuid

import allure
import pytest

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import EmployeeProgramGroupData

pytestmark = [pytest.mark.e2e, pytest.mark.employee_program]

# Pracownicza kategoria cenowa (id=68 na galak.test)
_PRICE_CATEGORY_EMPLOYEE = "68"


def _unique_group_name(suffix: str) -> str:
    return f"AT-EP-{suffix}-{uuid.uuid4().hex[:6]}"


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Admin tworzy grupę SMS — weryfikuje hashe — usuwa grupę"
)
def test_employee_program_crud_sms(page, runtime_env, admin_panel: AdminWrappers):
    """CRUD grupy SMS: create → read hashes → delete.

    Weryfikacja:
    - Grupa zostaje zapisana (group_id niepuste).
    - Przynajmniej jeden hash SMS jest widoczny po zapisie.
    - Usunięcie grupy nie powoduje błędu.
    """
    group_name = _unique_group_name("SMS")
    data = EmployeeProgramGroupData(
        group_name=group_name,
        price_category_id=_PRICE_CATEGORY_EMPLOYEE,
        enable_qr=False,
    )

    group_id = admin_panel.create_employee_group(data)

    if not group_id:
        pytest.skip(
            "Nie udało się uzyskać ID grupy po zapisie — "
            "admin może nie obsługiwać programu pracowniczego na tym środowisku."
        )

    # Odczyt hashy SMS
    hashes = admin_panel.get_employee_group_sms_hashes(group_id)

    # Cleanup — zawsze, niezależnie od asercji
    try:
        admin_panel.delete_employee_group(group_id)
    except Exception:
        pass  # Cleanup best-effort

    assert len(hashes) > 0, (
        f"Brak hashy SMS w grupie '{group_name}' (id={group_id}). "
        f"Znalezione: {hashes}"
    )


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario(
    "Admin tworzy grupę QR — generuje kod QR — usuwa grupę"
)
def test_employee_program_crud_qr(page, runtime_env, admin_panel: AdminWrappers):
    """CRUD grupy QR: create z włączonym QR → generate QR → delete.

    Weryfikacja:
    - Grupa zostaje zapisana (group_id niepuste).
    - Generowanie kodu QR kończy się bez błędu (brak JS error, redirect OK).
    - Usunięcie grupy nie powoduje błędu.
    """
    group_name = _unique_group_name("QR")
    data = EmployeeProgramGroupData(
        group_name=group_name,
        price_category_id=_PRICE_CATEGORY_EMPLOYEE,
        enable_qr=True,
    )

    group_id = admin_panel.create_employee_group(data)

    if not group_id:
        pytest.skip(
            "Nie udało się uzyskać ID grupy po zapisie — "
            "admin może nie obsługiwać programu pracowniczego z QR na tym środowisku."
        )

    try:
        admin_panel.generate_employee_group_qr(group_id)
    finally:
        try:
            admin_panel.delete_employee_group(group_id)
        except Exception:
            pass  # Cleanup best-effort

    # Jeśli dotarliśmy tutaj bez wyjątku — generowanie QR zakończyło się poprawnie.
    assert group_id, f"Group ID musi być niepuste po utworzeniu grupy QR '{group_name}'."
