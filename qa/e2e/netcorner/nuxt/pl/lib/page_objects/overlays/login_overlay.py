from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PwTimeoutError


class LoginOverlay:

    def __init__(self, page: Page):
        self.page = page
        self._root = page.locator('[data-name="loginForm"]')
        self._input_login = self._root.locator('#loginEmail')
        self._input_password = self._root.locator('#loginPassword')
        self._button_login = self._root.get_by_role(role='button', name='Zaloguj się')
        self._reset_password = self._root.get_by_text("Odzyskaj hasło", exact=True)
        self._register_account = self._root.locator('[href="/register"]')

    def enter_register_form(self) -> None:
        self._register_account.click()