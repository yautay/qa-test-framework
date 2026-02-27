from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from framework.env import RuntimeEnv
from playwright.sync_api import BrowserContext, Page

from qa.e2e.conftest import allure
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.toast_overlay import ToastObject, ToastType, ToastInstance
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.register_page import RegisterPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.register_user_data import RegisterUserData


def _step(title: str):
    return allure.step(title)


class RegistrationStatus(str, Enum):
    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass(frozen=True)
class RegistrationResult:
    status: RegistrationStatus
    toast: ToastObject | None = None
    my_account_visible: bool = False

    @property
    def is_success(self) -> bool:
        return self.status == RegistrationStatus.SUCCESS

    def __bool__(self) -> bool:
        return self.is_success


class FlowRegisterClient:
    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.page = page
        self.context = context
        self.runtime_env = runtime_env

    def register_new_client(self, user_data: RegisterUserData) -> RegistrationResult:
        with _step("Open home page"):
            home = HomePage(self.page, self.runtime_env.base_url)
            home.open().wait_loaded()

        with _step("Open login layer and select register form"):
            home.header.actions.open_login()
            home.overlays.login.enter_register_form()

        with _step(f"Fill registration form {user_data}"):
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

        with _step("Validate successful registration"):
            home_after_submit = HomePage(self.page, self.runtime_env.base_url)
            toast = home_after_submit.overlays.toast.get_toast(timeout=7_000)
            my_account_visible = home_after_submit.header.actions.is_my_account_available()

            if my_account_visible or (toast is not None and toast.instance == ToastInstance.USER_REGISTERED):
                return RegistrationResult(
                    status=RegistrationStatus.SUCCESS,
                    toast=toast,
                    my_account_visible=my_account_visible,
                )

            if toast is not None and (
                toast.instance == ToastInstance.FILL_FIELDS or toast.type in (ToastType.ERROR, ToastType.INFO)
            ):
                return RegistrationResult(
                    status=RegistrationStatus.VALIDATION_ERROR,
                    toast=toast,
                    my_account_visible=my_account_visible,
                )

            return RegistrationResult(
                status=RegistrationStatus.UNKNOWN_ERROR,
                toast=toast,
                my_account_visible=my_account_visible,
            )
