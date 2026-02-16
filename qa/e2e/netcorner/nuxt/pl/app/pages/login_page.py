from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.app.pages.base_page import BasePage
from qa.e2e.netcorner.nuxt.pl.app.selectors.nuxt_selectors import LoginSelectors


class LoginPage(BasePage):
    def submit(self) -> None:
        self.click(LoginSelectors.LOGIN_BUTTON)
