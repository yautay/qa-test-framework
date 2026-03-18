from __future__ import annotations

from contextlib import nullcontext

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.my_account_page import MyAccountPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.register_user_data import (
    RegisterUserCase,
    RegisterUserDataBuilder,
)

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "user_case",
    [
        RegisterUserCase(
            case_id="pl_password_change",
            factory=lambda: RegisterUserDataBuilder().with_required_terms().build(),
        )
    ],
    ids=lambda case: case.case_id,
)
@pytest.mark.scenario("Zmiana hasła użytkownika")
def test_password_change(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."
    home_page = HomePage(page, runtime_env.base_url).wait_loaded()
    home_page.header.actions.open_account()
    my_account = MyAccountPage(page, runtime_env.base_url).wait_loaded()
    my_account.content.menu_root.open_password_change()
    my_account.content.menu_change_password.change_password(user_data.password, user_data.password_changed)
    my_account.overlays.login.log_client(user_data.email, user_data.password_changed)
    my_account.header.actions.open_account()
    assert my_account.content.menu_root.get_logged_as() == user_data.email, "Użytkownik nie został poprawnie zalogowany"


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "user_case",
    [
        RegisterUserCase(
            case_id="pl_password_recovery",
            factory=lambda: RegisterUserDataBuilder().with_required_terms().build(),
        )
    ],
    ids=lambda case: case.case_id,
)
@pytest.mark.scenario("Odzyskiwanie hasła użytkownika")
def test_password_recovery(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."
    ClientWrappers(page, context, runtime_env).logout_client()
    home = HomePage(page, runtime_env.base_url)
    home.open().wait_loaded().header.actions.open_login()
    home.overlays.login.password_recovery(user_data.email)
    pass
