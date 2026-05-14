from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.admin.lib.page_objects.base_page import AdminBasePage, LoadState


class AdminLoginPage(AdminBasePage):
    """Admin panel login page.

    URL: <admin_base_url>/admin.php
    Confirmed live against komputronik-galak env (2026-05-14).

    Locators derived from live HTML inspection:
        <div class="content">
          <form id="loginForm" action="/admin.php/user/login/pl">
            <input type="text"     name="user_login"    id="user_login" />
            <input type="password" name="user_password" id="user_password" />
            <input type="submit"   name="commit" data-callback="submitForm" />
    """

    PAGE_ID = "netcorner.admin.login"
    PATH = "/admin.php"

    # Locators (confirmed live)
    _LOC_LOGIN_FORM = "#loginForm"
    _LOC_USERNAME = "#user_login"
    _LOC_PASSWORD = "#user_password"
    _LOC_SUBMIT = "input[data-callback='submitForm']"
    # Password-expiry reminder that can block login flow
    _LOC_PWD_REMINDER = "h2:has-text('Twoje hasło wygaśnie')"
    _LOC_PWD_REMINDER_CLOSE = "#sf_admin_footer ~ * input[value='Anuluj'], input[value='Anuluj']"
    # Indicator that login succeeded — the admin container is present
    _LOC_ADMIN_CONTAINER = "#sf_admin_container"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> AdminLoginPage:
        super().wait_loaded(state=state, timeout=timeout)
        return self

    def login(self, username: str, password: str) -> None:
        """Fill credentials and submit. Caller should navigate to login URL first via open()."""
        self.page.locator(self._LOC_USERNAME).fill(username)
        self.page.locator(self._LOC_PASSWORD).fill(password)
        self.page.locator(self._LOC_SUBMIT).click()
        self.page.wait_for_load_state("domcontentloaded")

        # Dismiss password-expiry reminder if present
        reminder = self.page.locator(self._LOC_PWD_REMINDER)
        if reminder.is_visible(timeout=3_000):
            close = self.page.locator(self._LOC_PWD_REMINDER_CLOSE)
            if close.count() > 0:
                close.first.click()
                self.page.wait_for_load_state("domcontentloaded")

    def is_login_form_visible(self) -> bool:
        return self.page.locator(self._LOC_LOGIN_FORM).is_visible(timeout=3_000)

    def is_logged_in(self) -> bool:
        """Returns True if we are past the login form (admin container is present)."""
        return self.page.locator(self._LOC_ADMIN_CONTAINER).is_visible(timeout=3_000)


__all__ = ["AdminLoginPage"]
