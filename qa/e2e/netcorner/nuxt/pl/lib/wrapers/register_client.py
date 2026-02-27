import importlib
from contextlib import nullcontext

<<<<<<< HEAD
from playwright.sync_api import BrowserContext, Page

from framework.env import RuntimeEnv
=======
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.toast_overlay import ToastType
>>>>>>> d615e89035a5152b89a0e0ba9a3e48e0a402ac46
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.register_page import RegisterPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.register_user_data import RegisterUserData

try:
    allure = importlib.import_module("allure")
except Exception:  # pragma: no cover - optional dependency
    allure = None


def _step(title: str):
    if allure is None:
        return nullcontext()
    return allure.step(title)


class FlowRegisterClient:
    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.page = page
        self.context = context
        self.runtime_env = runtime_env

    def register_new_client(self, user_data: RegisterUserData) -> bool:
<<<<<<< HEAD
        with _step("Open home page"):
            home = HomePage(self.page, self.runtime_env.base_url)
            home.open().wait_loaded()

        with _step("Open register form"):
            home.header.actions.open_login()
            home.overlays.login.enter_register_form()

        with _step("Fill registration form"):
            register_page = RegisterPage(self.page, self.runtime_env.base_url)
            register_page.wait_loaded()
            register_page.content.register_form.fill_login(user_data.email)
            if user_data.business_offer:
                register_page.content.register_form.check_business_offer()
                register_page.content.register_form.fill_business_personal_data(
                    nip=user_data.nip,
                    phone=user_data.phone,
                    email=user_data.email,
                )
            register_page.content.register_form.fill_password(user_data.password)
            register_page.content.register_form.fill_repeated_password(user_data.repeated_password)
            register_page.content.register_form.solve_captcha()

        with _step("Accept terms and submit"):
            if user_data.accept_marketing:
                register_page.content.register_form.accept_marketing_terms()
            if user_data.accept_required_terms:
                register_page.content.register_form.accept_required_terms()
            register_page.content.register_form.submit_registration()
        return True
=======
        home = HomePage(self.page, self.runtime_env.base_url)
        home.open().wait_loaded()
        home.header.actions.open_login()
        home.overlays.login.enter_register_form()
        register_page = RegisterPage(self.page, self.runtime_env.base_url)
        register_page.wait_loaded()
        register_page.content.register_form.fill_login(user_data.email)
        if user_data.business_offer:
            register_page.content.register_form.check_business_offer()
            register_page.content.register_form.fill_business_personal_data(nip=user_data.nip, phone=user_data.phone,
                                                                            email=user_data.email)
        register_page.content.register_form.fill_password(user_data.password)
        register_page.content.register_form.fill_repeated_password(user_data.repeated_password)
        register_page.content.register_form.solve_captcha()
        if user_data.accept_marketing:
            register_page.content.register_form.accept_marketing_terms()
        if user_data.accept_required_terms:
            register_page.content.register_form.accept_required_terms()
        register_page.content.register_form.submit_registration()
        toast = register_page.overlays.toast.get_toast()
        logged = register_page.header.actions.is_my_account_available()
        if toast.type == ToastType.SUCCESS and logged:
            return True
        return False
>>>>>>> d615e89035a5152b89a0e0ba9a3e48e0a402ac46
