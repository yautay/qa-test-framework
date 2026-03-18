from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class LoginOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="loginForm"]:visible').first, name="Login Overlay")
        self.__input_login = self.root.locator("#loginEmail")
        self.__input_password = self.root.locator("#loginPassword")
        self.__button_login = self.root.get_by_role(role="button", name="Zaloguj się")
        self.__reset_password = self.root.get_by_text("Odzyskaj hasło", exact=True)
        self.__register_account = self.root.locator('[href="/register"]')

    @step("Wchodzę w formularz rejestracji klienta.")
    def enter_register_form(self) -> None:
        self.wait_visible()
        self.safe_click(self.__register_account)

    @step("Loguję klienta loginem: {client_login} hasłem: {client_pwd}")
    def log_client(self, client_login: str, client_pwd: str) -> None:
        self.safe_type(self.__input_login, client_login)
        self.safe_type(self.__input_password, client_pwd)
        self.safe_click(self.__button_login)

    @step("Wybieram odzyskiwanie hasła dla loginu: {client_login}")
    def password_recovery(self, client_login: str) -> None:
        self.safe_click(self.__reset_password)
        pass
