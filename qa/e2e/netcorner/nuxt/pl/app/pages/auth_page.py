from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import AuthSelectors


class AuthPage(BasePage):
    def open_login_layer(self) -> None:
        self.click_first_visible([AuthSelectors.OPEN_LOGIN_LAYER_BUTTON])

    def try_login(self, email: str, password: str) -> bool:
        email_filled = self.fill_first_visible(AuthSelectors.LOGIN_EMAIL_INPUTS, email)
        password_filled = self.fill_first_visible(AuthSelectors.LOGIN_PASSWORD_INPUTS, password)
        if not (email_filled and password_filled):
            return False
        return self.click_first_visible(AuthSelectors.LOGIN_SUBMIT_BUTTONS)

    def continue_without_registration(self) -> bool:
        return self.click_first_visible(AuthSelectors.ORDER_WITHOUT_REGISTRATION_BUTTONS)
