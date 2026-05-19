from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.password_recovery_page import PasswordRecoveryPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import password_change_cases, password_recovery_cases

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize(
    "user_case",
    password_change_cases(),
    ids=lambda case: case.case_id,
)
@pytest.mark.scenario("Zmiana hasła użytkownika")
def test_password_change(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    dump_data(user_case=user_case, user_data=user_data)
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."
    home_page = HomePage(page, runtime_env.base_url).wait_loaded()
    my_account = home_page.open_account_page()
    my_account.open_password_change_page().content.menu_change_password.change_password(
        user_data.password,
        user_data.password_changed,
    )
    my_account.overlays.login.log_client(user_data.email, user_data.password_changed)
    my_account = my_account.open_account_page()
    assert my_account.content.menu_root.get_logged_as() == user_data.email, "Użytkownik nie został poprawnie zalogowany"


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize(
    "user_case",
    password_recovery_cases(),
    ids=lambda case: case.case_id,
)
@pytest.mark.scenario("Odzyskiwanie hasła użytkownika")
def test_password_recovery(page, context, runtime_env, user_case, mail_inbox: MailInboxService):
    user_data = user_case.factory()
    dump_data(user_case=user_case, user_data=user_data)
    assert ClientWrappers(page, context, runtime_env).register_new_client(
        user_data
    ), "Użytkownik nie został poprawnie zarejestrowany."

    consent_cookie_names = {"OptanonConsent", "OptanonAlertBoxClosed"}
    consent_cookies = [cookie for cookie in context.cookies() if cookie.get("name") in consent_cookie_names]
    context.clear_cookies()
    page.evaluate("() => { window.localStorage.clear(); window.sessionStorage.clear(); }")
    if consent_cookies:
        context.add_cookies(consent_cookies)

    home = HomePage(page, runtime_env.base_url)
    home.open().wait_loaded()
    home.open_login_overlay().password_recovery(user_data.email)
    reset_link = mail_inbox.get_password_reset_link(
        context=context,
        recipient=user_data.email,
    )
    page.goto(reset_link, wait_until="domcontentloaded")
    password_recovery = PasswordRecoveryPage(page, runtime_env.base_url).wait_loaded()
    assert (
        password_recovery.content.recovery_form.should_have_disabled_submit_button()
    ), "Przycisk Zapisz zmiany jest aktywny"
    (
        password_recovery.content.recovery_form.fill_new_password(user_data.password_changed)
        .fill_repeated_new_password(user_data.password_changed)
        .solve_captcha()
    )
    assert password_recovery.content.recovery_form.should_show_password_rules(), "Zasady tworzenia haseł niewidoczne"
    assert password_recovery.content.recovery_form.should_show_password_strength(), "Niewidoczny pasek siły hasła"
    assert (
        password_recovery.content.recovery_form.should_have_enabled_submit_button()
    ), "Przycisk Zapisz zmiany nie jest aktywny"
    password_recovery.content.recovery_form.submit_password_recovery()
    password_recovery.open_login_overlay().log_client(user_data.email, user_data.password_changed)
    my_account = password_recovery.open_account_page()
    assert my_account.content.menu_root.get_logged_as() == user_data.email, "Użutkownik jest niepoprawnie zalogowany"
