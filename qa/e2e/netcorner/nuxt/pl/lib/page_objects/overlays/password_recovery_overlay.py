from __future__ import annotations

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.timeouts import SLOW_OPERATION_MS, UI_ACTION_MS


class PasswordRecoveryOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="dialogContent"]:visible').first, name="Password Recovery Overlay")
        self.__input_login = self.root.locator("#resetPasswordEmail")
        self.__button_request_recovery = self.root.get_by_role(role="button", name="Wyślij")
        self.__button_confirm = self.root.get_by_role(role="button", name="Zrozumiałem")

    @step("Wypełniam formularz odzyskiwania hasła dla loginu: {client_login}")
    def password_recovery(self, client_login: str) -> None:
        self.wait_visible()
        self.safe_type(self.__input_login, client_login)
        self.__solve_captcha()
        self.__submit_form()

    @step("Klikam reCAPTCHA w odzyskiwaniu hasła")
    def __solve_captcha(self) -> None:
        frame = self.root.page.frame_locator('#recaptcha-password-reset iframe[title="reCAPTCHA"]')
        checkbox = frame.locator("#recaptcha-anchor")
        expect(checkbox).to_be_visible(timeout=UI_ACTION_MS)
        self.pointer_click(checkbox)
        expect(checkbox).to_have_attribute("aria-checked", "true", timeout=UI_ACTION_MS)

    @step("Wysyłam formularz odzyskiwania hasła")
    def __submit_form(self) -> None:
        self.pointer_click(self.__button_request_recovery)
        expect(self.__button_request_recovery).not_to_be_visible(timeout=SLOW_OPERATION_MS)
        self.pointer_click(self.__button_confirm)
