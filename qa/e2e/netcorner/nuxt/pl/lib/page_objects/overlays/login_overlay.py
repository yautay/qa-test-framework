from __future__ import annotations

from playwright.sync_api import Page
from playwright.sync_api import expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.password_recovery_overlay import (
    PasswordRecoveryOverlay,
)


class LoginOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="loginForm"]').first, name="Login Overlay")
        self.__input_login = self.root.locator("#loginEmail")
        self.__input_password = self.root.locator("#loginPassword")
        self.__button_login = self.root.get_by_role(role="button", name="Zaloguj się")
        self.__button_continue_without_login = self.root.get_by_role(
            role="button",
            name="Kontynuuj bez logowania",
        )
        self.__reset_password = self.root.get_by_text("Odzyskaj hasło", exact=True)
        self.__register_account = self.root.locator('[href="/register"]')

    def wait_visible(self, timeout: int | None = None) -> LoginOverlay:
        super().wait_visible(timeout=timeout)
        t = timeout or self.DEFAULT_TIMEOUT
        expect(self.__input_login.first).to_be_visible(timeout=t)
        expect(self.__input_password.first).to_be_visible(timeout=t)
        return self

    @step("Wchodzę w formularz rejestracji klienta.")
    def enter_register_form(self) -> None:
        self.wait_visible()
        self.pointer_click(self.__register_account)

    @step("Loguję klienta loginem: {client_login} hasłem: {client_pwd}")
    def log_client(self, client_login: str, client_pwd: str) -> None:
        self.safe_type(self.__input_login, client_login)
        self.safe_type(self.__input_password, client_pwd)
        self.pointer_click(self.__button_login)

    @step("Kontynuuję bez logowania, jeśli pojawił się modal logowania")
    def continue_without_login_if_visible(self, timeout: int = 3_000) -> bool:
        try:
            self.wait_visible(timeout=timeout)
        except AssertionError:
            return False

        self.pointer_click(self.__button_continue_without_login)
        self.wait_hidden()
        return True

    @step("Odzyskuję hasło")
    def password_recovery(self, client_login: str) -> None:
        self.pointer_click(self.__reset_password)
        PasswordRecoveryOverlay(self.root.page).password_recovery(client_login)
