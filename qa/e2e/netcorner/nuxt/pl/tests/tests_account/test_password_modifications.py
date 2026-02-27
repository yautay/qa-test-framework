from __future__ import annotations

import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.my_account_page import MyAccountPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.register_user_data import valid_client_cases, invalid_client_cases, \
    RegisterUserCase, RegisterUserDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.wrapers.register_client import FlowRegisterClient
from qa.scenario import scenario

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.account]


@pytest.mark.parametrize(
    "user_case",
    [RegisterUserCase(
        case_id="pl_password_recovery",
        factory=lambda: (
                RegisterUserDataBuilder().with_required_terms().build()
        ),
    )],
    ids=lambda case: case.case_id
)
@scenario("Account Tests: Zmiana hasła")
def test_password_change(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    assert FlowRegisterClient(page, context, runtime_env).register_new_client(user_data),\
        f"Użytkownik nie został poprawnie zarejestrowany."
    home_page = HomePage(page, runtime_env.base_url).wait_loaded()
    home_page.header.actions.open_account()
    my_account = MyAccountPage(page, runtime_env.base_url).wait_loaded()
    my_account.content.menu_root.open_password_change()
    my_account.content.menu_change_password.change_password(user_data.password, user_data.password_changed)
    home_page.open().wait_loaded().header.actions.open_login()
    home_page.overlays.login.log_client(user_data.email, user_data.password_changed)
    home_page.header.actions.open_account()
    assert my_account.content.menu_root.get_logged_as() == user_data.email, "Użytkownik nie został poprawnie zalogowany"