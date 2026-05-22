from __future__ import annotations

import uuid

import allure
import pytest

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.lib.step_api import step_context
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import EmployeeProgramGroupData
from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService
from qa.e2e.netcorner.mailhog.lib.mail_subjects import MailSubjectPattern
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.register_page import RegisterPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_employee_program,
    pytest.mark.xdist_group("employee_program_serial"),
]

_PRICE_CATEGORY_EMPLOYEE = "75"
_MAIL_EMPLOYEE_RECIPIENT = "sklep@komputronik.pl"
_EMPLOYEE_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*(program-pracowniczy|partnerEmployeeGroup/register|employee|/pel/)[^\s\"'<>]*"


def _unique_group_name(suffix: str) -> str:
    return f"AT-EP-{suffix}-{uuid.uuid4().hex[:6]}"


def _employee_group_data(*, group_name: str, enable_qr: bool) -> EmployeeProgramGroupData:
    return EmployeeProgramGroupData(
        group_name=group_name,
        price_category_id=_PRICE_CATEGORY_EMPLOYEE,
        enable_qr=enable_qr,
    )


def _employee_mail_subject() -> MailSubjectPattern:
    return MailSubjectPattern(
        key="employee_program_link",
        regex=r"(?i)^.*(pracownik|partner).*$",
        description="Mail z linkiem do programu pracowniczego",
    )


def _assert_user_registered_in_program(page, admin_panel: AdminWrappers, email: str) -> None:
    admin_panel.navigate_to("partnerEmployeeGroupCustomer/list/pl")
    assert page.locator(f"td:has-text('{email}')").first.count() > 0, (
        f"Email '{email}' nie znaleziony na liście pracowników programu pracowniczego."
    )


def _login_from_employee_link(page, runtime_env, email: str, password: str, link: str) -> None:
    page.goto(link, wait_until="domcontentloaded")
    cookie_accept = page.locator("#onetrust-accept-btn-handler")
    if cookie_accept.count() and cookie_accept.first.is_visible():
        cookie_accept.first.click(force=True)
    home = HomePage(page, runtime_env.base_url)
    home.overlays.login.wait_visible().log_client(email, password)
    logged_as = home.open_account_page().content.menu_root.get_logged_as()
    assert logged_as == email, f"Nie udało się zalogować użytkownika '{email}' z linku programu pracowniczego."


def _enable_recaptcha_test_cookie(context, page, base_url: str) -> None:
    context.add_cookies([{"name": "recaptcha_test", "value": "on", "url": base_url}])
    page.goto(base_url, wait_until="domcontentloaded")


def _register_client_from_login_layer(page, runtime_env, user_data, employee_link: str) -> None:
    register_link = f"{employee_link.rstrip('/')}/register"
    page.goto(register_link, wait_until="domcontentloaded")
    register_page = RegisterPage(page, runtime_env.base_url).wait_loaded()
    form = register_page.content.register_form
    form.fill_login(user_data.email)
    form.fill_password(user_data.password)
    form.fill_repeated_password(user_data.password)
    form.solve_captcha()
    if user_data.accept_marketing:
        form.accept_marketing_terms()
    if user_data.accept_required_terms:
        form.accept_required_terms()
    form.submit_registration()
    logged_as = HomePage(page, runtime_env.base_url).open_account_page().content.menu_root.get_logged_as()
    assert logged_as == user_data.email, f"Użytkownik '{user_data.email}' nie został zalogowany po rejestracji."


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Klient loguje się do programu pracowniczego SMS")
def test_employee_program_login_sms(page, context, runtime_env, admin_panel: AdminWrappers, mail_inbox: MailInboxService):
    with step_context("Tworzę grupę SMS programu pracowniczego"):
        group_id = admin_panel.create_employee_group(_employee_group_data(group_name=_unique_group_name("LOGIN-SMS"), enable_qr=False))
        assert group_id, "Nie udało się utworzyć grupy SMS w adminie."

    user_data = ClientDataBuilder().with_required_terms().build()
    try:
        with step_context("Włączam testowy cookie dla reCAPTCHA"):
            _enable_recaptcha_test_cookie(context, page, runtime_env.base_url)
        with step_context("Rejestruję klienta i pobieram link SMS"):
            assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), "Rejestracja klienta nie powiodła się."
            employee_link = mail_inbox.get_link_from_subject(
                context=context,
                recipient=_MAIL_EMPLOYEE_RECIPIENT,
                subject=_employee_mail_subject(),
                link_regex=_EMPLOYEE_LINK_REGEX,
            )
        with step_context("Loguję klienta przez link programu i weryfikuję przypisanie do grupy"):
            _login_from_employee_link(page, runtime_env, user_data.email, user_data.password, employee_link)
            _assert_user_registered_in_program(page, admin_panel, user_data.email)
    finally:
        if group_id:
            admin_panel.delete_employee_group(group_id)


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Klient rejestruje się do programu pracowniczego SMS")
def test_employee_program_register_sms(page, context, runtime_env, admin_panel: AdminWrappers, mail_inbox: MailInboxService):
    with step_context("Tworzę grupę SMS programu pracowniczego"):
        group_id = admin_panel.create_employee_group(_employee_group_data(group_name=_unique_group_name("REGISTER-SMS"), enable_qr=False))
        assert group_id, "Nie udało się utworzyć grupy SMS w adminie."

    user_data = ClientDataBuilder().with_required_terms().build()
    try:
        with step_context("Włączam testowy cookie dla reCAPTCHA"):
            _enable_recaptcha_test_cookie(context, page, runtime_env.base_url)
        with step_context("Pobieram link SMS i przechodzę do flow rejestracji"):
            employee_link = mail_inbox.get_link_from_subject(
                context=context,
                recipient=_MAIL_EMPLOYEE_RECIPIENT,
                subject=_employee_mail_subject(),
                link_regex=_EMPLOYEE_LINK_REGEX,
            )
            page.goto(employee_link, wait_until="domcontentloaded")
        with step_context("Rejestruję klienta i weryfikuję przypisanie do grupy"):
            _register_client_from_login_layer(page, runtime_env, user_data, employee_link)
            _assert_user_registered_in_program(page, admin_panel, user_data.email)
    finally:
        if group_id:
            admin_panel.delete_employee_group(group_id)


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Klient loguje się do programu pracowniczego QR")
def test_employee_program_login_qr(page, context, runtime_env, admin_panel: AdminWrappers):
    with step_context("Tworzę grupę QR programu pracowniczego"):
        group_id = admin_panel.create_employee_group(_employee_group_data(group_name=_unique_group_name("LOGIN-QR"), enable_qr=True))
        assert group_id, "Nie udało się utworzyć grupy QR w adminie."

    user_data = ClientDataBuilder().with_required_terms().build()
    try:
        with step_context("Włączam testowy cookie dla reCAPTCHA"):
            _enable_recaptcha_test_cookie(context, page, runtime_env.base_url)
        with step_context("Rejestruję klienta i pobieram link QR"):
            assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), "Rejestracja klienta nie powiodła się."
            employee_link = admin_panel.get_employee_group_qr_value(group_id)
            assert employee_link.startswith("http"), f"QR nie zwrócił poprawnego linku logowania: '{employee_link[:120]}'"
        with step_context("Loguję klienta przez link programu i weryfikuję przypisanie do grupy"):
            _login_from_employee_link(page, runtime_env, user_data.email, user_data.password, employee_link)
            _assert_user_registered_in_program(page, admin_panel, user_data.email)
    finally:
        if group_id:
            admin_panel.delete_employee_group(group_id)


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Klient rejestruje się do programu pracowniczego QR")
def test_employee_program_register_qr(page, context, runtime_env, admin_panel: AdminWrappers):
    with step_context("Tworzę grupę QR programu pracowniczego"):
        group_id = admin_panel.create_employee_group(_employee_group_data(group_name=_unique_group_name("REGISTER-QR"), enable_qr=True))
        assert group_id, "Nie udało się utworzyć grupy QR w adminie."

    user_data = ClientDataBuilder().with_required_terms().build()
    try:
        with step_context("Włączam testowy cookie dla reCAPTCHA"):
            _enable_recaptcha_test_cookie(context, page, runtime_env.base_url)
        with step_context("Pobieram link QR i przechodzę do flow rejestracji"):
            employee_link = admin_panel.get_employee_group_qr_value(group_id)
            assert employee_link.startswith("http"), f"QR nie zwrócił poprawnego linku rejestracji: '{employee_link[:120]}'"
            page.goto(employee_link, wait_until="domcontentloaded")
        with step_context("Rejestruję klienta i weryfikuję przypisanie do grupy"):
            _register_client_from_login_layer(page, runtime_env, user_data, employee_link)
            _assert_user_registered_in_program(page, admin_panel, user_data.email)
    finally:
        if group_id:
            admin_panel.delete_employee_group(group_id)
