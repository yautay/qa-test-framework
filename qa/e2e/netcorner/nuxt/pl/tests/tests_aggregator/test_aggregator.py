from __future__ import annotations

import uuid

import allure
import pytest
from playwright.sync_api import expect

from qa.e2e.netcorner.nuxt.pl.tests.helpers import accept_cookie_banner_if_visible, open_home_and_accept_cookies

pytestmark = [pytest.mark.e2e, pytest.mark.orders]


@allure.feature("Agregator")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Agregator produktowy utworzony w adminie jest widoczny na froncie")
def test_aggregator(page, runtime_env, admin_panel):
    suffix = uuid.uuid4().hex[:8]
    frontend_url = admin_panel.create_products_aggregator(
        name=f"Agregator produkty {suffix}",
        work_name=f"Agregator produkty {suffix}",
        url_slug=f"agregator-products-{suffix}",
        item_name="Klawiatury",
        section_code="Agregator",
        product_codes="KL-NAT-038,KL-LOG-094,LT-STD-I15-DEL-1300",
    )

    open_home_and_accept_cookies(page, runtime_env.base_url)
    page.goto(frontend_url, wait_until="domcontentloaded")
    accept_cookie_banner_if_visible(page)

    expect(page.locator("[data-name='aggregatorSlider']")).to_be_visible(timeout=15_000)
    assert page.locator("[data-name='cardProduct']").count() > 0, "Agregator nie wyświetlił żadnych produktów na froncie."
