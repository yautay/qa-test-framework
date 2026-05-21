from __future__ import annotations

import uuid

import allure
import pytest

from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.lib.step_api import step_context
from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService
from qa.e2e.netcorner.mailhog.lib.mail_subjects import MailSubjectPattern
from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import EmployeeProgramGroupData
from qa.e2e.netcorner.nuxt.pl.lib.flows.cart_and_checkout_wrappers import CartAndCheckoutWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.flows.select_product_wrappers import SelectProductWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkouts_generators import (
    checkout_payment_blik_required_terms,
    private_person_checkout_purchaser,
    private_person_delivery_courier_receiver,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_generators import ClientDataBuilder
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listings_data_models import ListingsData
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import AvailabilityStatuses

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_employee_program]

_PRICE_CATEGORY_EMPLOYEE = "75"
_MAIL_EMPLOYEE_RECIPIENT = "sklep@komputronik.pl"
_EMPLOYEE_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*(program-pracowniczy|partnerEmployeeGroup/register|employee|/pel/)[^\s\"'<>]*"
_EMPLOYEE_PRICE_CATEGORY_TEXT = "Cena Program Partnerski dla firm"


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


def _router_listing_case() -> ListingsData:
    return ListingsData(
        category_url="category/2371/routery.html",
        product_availability_status=AvailabilityStatuses.ONE_DAY,
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


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Zamówienie w programie pracowniczym SMS")
def test_employee_program_order_sms(page, context, runtime_env, admin_panel: AdminWrappers, mail_inbox: MailInboxService):
    with step_context("Tworzę grupę SMS programu pracowniczego"):
        group_id = admin_panel.create_employee_group(_employee_group_data(group_name=_unique_group_name("ORD-SMS"), enable_qr=False))
        assert group_id, "Nie udało się utworzyć grupy SMS."

    user_data = ClientDataBuilder().with_required_terms().build()
    try:
        with step_context("Włączam testowy cookie dla reCAPTCHA"):
            _enable_recaptcha_test_cookie(context, page, runtime_env.base_url)
        with step_context("Rejestruję klienta i pobieram link SMS programu"):
            assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), "Rejestracja klienta nie powiodła się."
            employee_link = mail_inbox.get_link_from_subject(
                context=context,
                recipient=_MAIL_EMPLOYEE_RECIPIENT,
                subject=_employee_mail_subject(),
                link_regex=_EMPLOYEE_LINK_REGEX,
            )
        with step_context("Loguję klienta i dodaję produkt z kategorii routerów"):
            _login_from_employee_link(page, runtime_env, user_data.email, user_data.password, employee_link)
            selected = SelectProductWrappers(page, context, runtime_env).select_test_product(_router_listing_case())
            assert selected is not None and selected.product_page_data is not None, "Nie udało się dodać produktu do koszyka."

        checkout = CartAndCheckoutWrappers(page, context, runtime_env)
        checkout.process_cart()
        result = checkout.process_checkout(
            private_person_delivery_courier_receiver().delivery_type,
            private_person_delivery_courier_receiver(),
            private_person_checkout_purchaser(),
            checkout_payment_blik_required_terms(),
        )
        order_number = result.typ_summary_data.order_number.strip()
        assert order_number, "Zamówienie SMS (pracownicze) nie zostało złożone."

        with step_context("Weryfikuję zamówienie w panelu admin"):
            order_data = admin_panel.get_order_data(order_number)
            products_text = admin_panel.get_order_products_raw_text(order_number)
            assert _EMPLOYEE_PRICE_CATEGORY_TEXT in products_text, (
                f"Brak oznaczenia kategorii ceny pracowniczej ('{_EMPLOYEE_PRICE_CATEGORY_TEXT}') "
                f"w sekcji produktów zamówienia '{order_number}'."
            )
    finally:
        if group_id:
            admin_panel.delete_employee_group(group_id)


@allure.feature("Program pracowniczy")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.scenario("Zamówienie w programie pracowniczym QR")
def test_employee_program_order_qr(page, context, runtime_env, admin_panel: AdminWrappers):
    with step_context("Tworzę grupę QR programu pracowniczego"):
        group_id = admin_panel.create_employee_group(_employee_group_data(group_name=_unique_group_name("ORD-QR"), enable_qr=True))
        assert group_id, "Nie udało się utworzyć grupy QR."

    user_data = ClientDataBuilder().with_required_terms().build()
    try:
        with step_context("Włączam testowy cookie dla reCAPTCHA"):
            _enable_recaptcha_test_cookie(context, page, runtime_env.base_url)
        with step_context("Rejestruję klienta i pobieram link QR programu"):
            assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), "Rejestracja klienta nie powiodła się."
            employee_link = admin_panel.get_employee_group_qr_value(group_id)
            assert employee_link.startswith("http"), f"QR nie zwrócił poprawnego linku logowania: '{employee_link[:120]}'"
        with step_context("Loguję klienta i dodaję produkt z kategorii routerów"):
            _login_from_employee_link(page, runtime_env, user_data.email, user_data.password, employee_link)
            selected = SelectProductWrappers(page, context, runtime_env).select_test_product(_router_listing_case())
            assert selected is not None and selected.product_page_data is not None, "Nie udało się dodać produktu do koszyka."

        checkout = CartAndCheckoutWrappers(page, context, runtime_env)
        checkout.process_cart()
        result = checkout.process_checkout(
            private_person_delivery_courier_receiver().delivery_type,
            private_person_delivery_courier_receiver(),
            private_person_checkout_purchaser(),
            checkout_payment_blik_required_terms(),
        )
        order_number = result.typ_summary_data.order_number.strip()
        assert order_number, "Zamówienie QR (pracownicze) nie zostało złożone."

        with step_context("Weryfikuję zamówienie w panelu admin"):
            order_data = admin_panel.get_order_data(order_number)
            products_text = admin_panel.get_order_products_raw_text(order_number)
            assert _EMPLOYEE_PRICE_CATEGORY_TEXT in products_text, (
                f"Brak oznaczenia kategorii ceny pracowniczej ('{_EMPLOYEE_PRICE_CATEGORY_TEXT}') "
                f"w sekcji produktów zamówienia '{order_number}'."
            )
    finally:
        if group_id:
            admin_panel.delete_employee_group(group_id)
