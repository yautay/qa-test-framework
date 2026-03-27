from __future__ import annotations

from contextlib import nullcontext

from playwright.sync_api import BrowserContext, Page

from framework.env import RuntimeEnv
from qa.e2e.conftest import allure
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.my_account_page import MyAccountPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.register_page import RegisterPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import ClientData


def _step(title: str):
    if allure is None:
        return nullcontext()
    return allure.step(title)


class ClientWrappers:
    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.__page = page
        self.__context = context
        self.__runtime_env = runtime_env

    def register_new_client(self, user_data: ClientData) -> bool:
        home = HomePage(self.__page, self.__runtime_env.base_url)
        with _step("Otwieram stronę główną"):
            home = HomePage(self.__page, self.__runtime_env.base_url)
            home.open().wait_loaded()

        with _step("Otwieram panel logowania i wybieram formularz rejestracji"):
            home.header.actions.open_login()
            home.overlays.login.enter_register_form()

        with _step(f"Wypełniam formularz rejestracji {user_data}"):
            register_page = RegisterPage(self.__page, self.__runtime_env.base_url)
            register_page.wait_loaded().content.register_form.fill_login(user_data.email)
            if user_data.business_offer:
                register_page.content.register_form.check_business_offer()
                register_page.content.register_form.fill_business_personal_data(
                    nip=user_data.nip,
                    phone=user_data.phone,
                    email=user_data.email,
                )
            register_page.content.register_form.fill_password(user_data.password)
            register_page.content.register_form.fill_repeated_password(user_data.password)
            register_page.content.register_form.solve_captcha()

        with _step("Akceptuję zgody i wysyłam formularz"):
            if user_data.accept_marketing:
                register_page.content.register_form.accept_marketing_terms()
            if user_data.accept_required_terms:
                register_page.content.register_form.accept_required_terms()
            register_page.content.register_form.submit_registration()

        with _step("Weryfikuję poprawną rejestrację"):
            home_after_submit = HomePage(self.__page, self.__runtime_env.base_url)
            home_after_submit.overlays.toast.get_toast(timeout=5_000)
            my_account_visible = home_after_submit.header.actions.is_my_account_available()
            if my_account_visible:
                home.header.actions.open_account()
                logged_as = (
                    MyAccountPage(self.__page, self.__runtime_env.base_url)
                    .wait_loaded()
                    .content.menu_root.get_logged_as()
                )
                if logged_as == user_data.email:
                    return True
            return False

    def logout_client(self):
        home = HomePage(self.__page, self.__runtime_env.base_url)
        with _step("Otwieram 'Moje Konto'"):
            home.open()
            home.wait_loaded()
            home.header.actions.open_account()

        with _step("Klikam przycisk 'wyloguj'"):
            MyAccountPage(self.__page, self.__runtime_env.base_url).content.menu_root.logout()
