from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import AdminOrdersReportsPage

pytestmark = [pytest.mark.e2e]


@allure.feature("Admin")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Lista zamówień w adminie udostępnia dane i akcje raportowe")
def test_admin_reports(page, runtime_env, admin_panel):
    reports_page = AdminOrdersReportsPage(page, admin_panel.admin_env.base_url)
    admin_panel.open_admin()
    reports_page.navigate_to()

    order_numbers = reports_page.get_recent_order_numbers(limit=5)
    assert order_numbers, "Lista zamówień w adminie nie zwróciła żadnych numerów zamówień do raportowania."

    report_actions = reports_page.get_report_action_texts()
    assert len(report_actions) >= 4, (
        "Na stronie raportów zamówień nie znaleziono pełnego zestawu akcji eksportu/raportów. "
        f"Znaleziono: {report_actions}"
    )
