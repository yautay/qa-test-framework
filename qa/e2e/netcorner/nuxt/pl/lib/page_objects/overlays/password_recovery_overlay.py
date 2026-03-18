from __future__ import annotations

from contextlib import nullcontext

from playwright.sync_api import Page
from qa.e2e.conftest import allure
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class PasswordRecoveryOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="dialogContent"]:visible').first, name="Password Recovery Overlay")
        self.__input_login = self.root.locator("#resetPasswordEmail")
        self.__button_request_recovery = self.root.get_by_role(role="button", name="Wyślij")

    @step("Wypełniam formularz odzyskiwania hasła dla loginu: {client_login}")
    def password_recovery(self, client_login: str) -> None:
        self.safe_type(self.__input_login, client_login)
        # TODO recaptcha solve
        # TODO submit form

