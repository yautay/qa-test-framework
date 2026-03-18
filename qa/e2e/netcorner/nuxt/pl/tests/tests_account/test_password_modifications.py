from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.my_account_page import MyAccountPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.password_recovery_page import PasswordRecoveryPage
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
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Użytkownik nie został poprawnie zarejestrowany."
    )
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
def test_password_recovery(page, context, runtime_env, user_case, mail_inbox: MailInboxService):
    user_data = user_case.factory()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Użytkownik nie został poprawnie zarejestrowany."
    )
    ClientWrappers(page, context, runtime_env).logout_client()
    home = HomePage(page, runtime_env.base_url)
    home.open().wait_loaded().header.actions.open_login()
    home.overlays.login.password_recovery(user_data.email)
    reset_link = mail_inbox.get_password_reset_link(
        context=context,
        recipient=user_data.email,
    )
    page.goto(reset_link, wait_until="domcontentloaded")
    password_recovery = PasswordRecoveryPage(page, runtime_env.base_url).wait_loaded()
    assert password_recovery.content.recovery_form.should_have_disabled_submit_button(), \
        "Przycisk Zapisz zmiany jest aktywny"
    (password_recovery.content.recovery_form.fill_new_password(user_data.password_changed)
     .fill_repeated_new_password(user_data.password_changed).solve_captcha())
    assert password_recovery.content.recovery_form.should_show_password_rules(), "Zasady tworzenia haseł niewidoczne"
    assert password_recovery.content.recovery_form.should_show_password_strength(), "Niewidoczny pasek siły hasła"
    assert password_recovery.content.recovery_form.should_have_enabled_submit_button(), "Przycisk Zapisz zmiany nie jest aktywny"
    password_recovery.content.recovery_form.submit_password_recovery()
    password_recovery.header.actions.open_login()
    password_recovery.overlays.login.log_client(user_data.email, user_data.password_changed)
    password_recovery.header.actions.open_account()
    assert MyAccountPage(page, runtime_env.base_url).content.menu_root.get_logged_as() == user_data.email, \
        "Użutkownik jest niepoprawnie zalogowany"
