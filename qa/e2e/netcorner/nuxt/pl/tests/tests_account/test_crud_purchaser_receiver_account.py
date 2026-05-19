from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Sekcje nabywcy i odbiorcy są dostępne w panelu konta")
def test_crud_purchaser_receiver_account(page, context, runtime_env):
    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Nie udało się przygotować użytkownika do testu CRUD w koncie."
    )

    account = HomePage(page, runtime_env.base_url).open_account_page()

    # Purchasers — nawigacja + weryfikacja dostępności sekcji
    account.content.menu_root.open_purchasers()
    page.wait_for_url("**/customer/account/purchasers", timeout=10_000)
    assert "/customer/account/purchasers" in page.url, (
        "Sekcja nabywców nie jest dostępna — strona nie załadowała się po kliknięciu linku menu."
    )
    assert page.get_by_role("heading", name="Lista danych do faktur").is_visible(), (
        "Brak nagłówka 'Lista danych do faktur' na stronie nabywców."
    )

    # Receivers — wróć do konta i nawiguj do odbiorców
    HomePage(page, runtime_env.base_url).open_account_page().content.menu_root.open_receivers()
    page.wait_for_url("**/customer/account/receivers", timeout=10_000)
    assert "/customer/account/receivers" in page.url, (
        "Sekcja odbiorców nie jest dostępna — strona nie załadowała się po kliknięciu linku menu."
    )
    assert page.get_by_role("heading", name="Lista danych do dostawy").is_visible(), (
        "Brak nagłówka 'Lista danych do dostawy' na stronie odbiorców."
    )
