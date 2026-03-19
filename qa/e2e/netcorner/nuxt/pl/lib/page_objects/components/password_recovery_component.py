from __future__ import annotations

from playwright.sync_api import Locator, expect

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step


class PasswordRecoveryComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Password Recovery Component")

        self.__input_new_password = self.find("#newPassword")
        self.__input_new_password_repeated = self.find("#newPasswordRepeated")

        self.__password_strength = self.find('[data-name="passwordStrength"]')
        self.__password_rules = self.root.locator("ol.list-decimal")

        self.__recaptcha_container = self.find("#recaptcha-password-recovery")

        self.__button_save_changes = self.find('button:has-text("Zapisz zmiany")')

    # ============================================================
    # ACTIONS
    # ============================================================

    @step("Ustawiam nowe hasło: {password}")
    def fill_new_password(self, password: str) -> "PasswordRecoveryComponent":
        self.safe_type(self.__input_new_password, password)
        return self

    @step("Powtarzam nowe hasło: {password}")
    def fill_repeated_new_password(self, password: str) -> "PasswordRecoveryComponent":
        self.safe_type(self.__input_new_password_repeated, password)
        return self

    @step("Ustawiam nowe hasło: {password} i jego powtórzenie")
    def fill_passwords(self, password: str) -> "PasswordRecoveryComponent":
        self.fill_new_password(password)
        self.fill_repeated_new_password(password)
        return self

    @step("Klikam reCAPTCHA, by potwierdzić, że nie jestem botem")
    def solve_captcha(self) -> "PasswordRecoveryComponent":
        frame = self.root.page.frame_locator('#recaptcha-password-recovery iframe[title="reCAPTCHA"]')
        checkbox = frame.locator("#recaptcha-anchor")
        expect(checkbox).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        checkbox.click(timeout=self.DEFAULT_TIMEOUT)
        return self

    @step("Klikam przycisk 'Zapisz zmiany'")
    def submit_password_recovery(self) -> None:
        self.safe_click(self.__button_save_changes)

    # ============================================================
    # ASSERTIONS / HELPERS
    # ============================================================

    @step("Sprawdzam, czy przycisk 'Zapisz zmiany' jest zablokowany")
    def should_have_disabled_submit_button(self) -> "PasswordRecoveryComponent":
        expect(self.__button_save_changes).to_be_disabled()
        return self

    @step("Sprawdzam, czy przycisk 'Zapisz zmiany' jest aktywny")
    def should_have_enabled_submit_button(self) -> "PasswordRecoveryComponent":
        expect(self.__button_save_changes).to_be_enabled()
        return self

    @step("Sprawdzam widoczność sekcji siły hasła")
    def should_show_password_strength(self) -> "PasswordRecoveryComponent":
        expect(self.__password_strength).to_be_visible()
        return self

    @step("Sprawdzam widoczność zasad tworzenia hasła")
    def should_show_password_rules(self) -> "PasswordRecoveryComponent":
        expect(self.__password_rules).to_be_visible()
        return self