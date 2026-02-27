from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PwTimeoutError, expect

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class LoginOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="loginForm"]'), name="Login Overlay")
        self._input_login = self.root.locator('#loginEmail')
        self._input_password = self.root.locator('#loginPassword')
        self._button_login = self.root.get_by_role(role='button', name='Zaloguj się')
        self._reset_password = self.root.get_by_text("Odzyskaj hasło", exact=True)
        self._register_account = self.root.locator('[href="/register"]')

    def enter_register_form(self) -> None:
        self.wait_visible()
        self._register_account.click()