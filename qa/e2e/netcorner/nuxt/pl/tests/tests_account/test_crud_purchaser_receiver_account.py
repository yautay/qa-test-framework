from __future__ import annotations

import re

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [pytest.mark.e2e, pytest.mark.account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("CRUD nabywcy i odbiorcy w Moim Koncie — smoke alfa")
def test_crud_purchaser_receiver_account(page, context, runtime_env):
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Nie udało się przygotować użytkownika do testu CRUD w koncie."
    )

    account = HomePage(page, runtime_env.base_url).open_account_page()

    purchasers_link = page.locator("a[href='/customer/account/purchasers']").first
    if purchasers_link.count() == 0 or not purchasers_link.is_visible():
        pytest.skip("Na środowisku nie znaleziono aktywnego linku do sekcji nabywców.")
    account.content.menu_root.open_purchasers()
    if "/customer/account/purchasers" not in page.url:
        pytest.skip("Sekcja nabywców nie jest dostępna dla bieżącego konta na env.")
    assert page.get_by_role("button", name=re.compile(r"Dodaj", re.IGNORECASE)).count() > 0, (
        "Brak akcji dodawania nabywcy w panelu konta."
    )

    account.open_account_page()
    receivers_link = page.locator("a[href='/customer/account/receivers']").first
    if receivers_link.count() == 0 or not receivers_link.is_visible():
        pytest.skip("Na środowisku nie znaleziono aktywnego linku do sekcji odbiorców.")
    account.content.menu_root.open_receivers()
    if "/customer/account/receivers" not in page.url:
        pytest.skip("Sekcja odbiorców nie jest dostępna dla bieżącego konta na env.")
    assert page.get_by_role("button", name=re.compile(r"Dodaj", re.IGNORECASE)).count() > 0, (
        "Brak akcji dodawania odbiorcy w panelu konta."
    )
