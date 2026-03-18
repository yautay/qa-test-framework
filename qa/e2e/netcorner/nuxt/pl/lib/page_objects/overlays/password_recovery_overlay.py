from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class PasswordRecoveryOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="dialogContent"]:visible').first, name="Password Recovery Overlay")
        self.__input_login = self.root.locator("#resetPasswordEmail")
        self.__button_request_recovery = self.root.get_by_role(role="button", name="Wyślij")
        self.__buton_confirm = self.root.get_by_role(role="button", name="Zrozumiałem")

    @step("Wypełniam formularz odzyskiwania hasła dla loginu: {client_login}")
    def password_recovery(self, client_login: str) -> None:
        self.wait_visible()
        self.safe_type(self.__input_login, client_login)
        self.__solve_captcha()
        self.__submit_form()

    @step("Klikam reCAPTCHA w odzyskiwaniu hasła")
    def __solve_captcha(self) -> None:
        frame = self.root.page.frame_locator('iframe[title="reCAPTCHA"]')
        checkbox = frame.locator("#recaptcha-anchor")
        self.safe_click(checkbox)

    @step("Wysyłam formularz odzyskiwania hasła")
    def __submit_form(self) -> None:
        self.safe_click(self.__button_request_recovery)
        self.safe_click(self.__buton_confirm)
