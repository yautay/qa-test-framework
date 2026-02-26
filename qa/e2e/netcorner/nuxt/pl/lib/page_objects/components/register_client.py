from __future__ import annotations

from playwright.sync_api import expect, Locator
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class RegisterClient(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Register Client Component")

        # --- pola podstawowe ---
        self._input_login = self.find('#login')
        self._input_password = self.find('#password')
        self._input_password_repeated = self.find('#passwordRepeated')

        # --- checkboxy ---
        self._checkbox_business_offer = self.find('#businessOffer')
        self._checkbox_terms = self.find('#customer_company_rules_terms')
        self._checkbox_marketing = self.find('#customer_marketing_terms')

        # --- captcha ---
        self._recaptcha_container = self.find('#recaptcha-register')

        # --- przyciski ---
        self._button_register = self.find('button:has-text("Załóż konto")')
        self._button_login_redirect = self.find('button:has-text("Masz już konto? Zaloguj się.")')

        # --- business section root ---
        self._business_section = self.find('#businessOffer').locator(
            'xpath=ancestor::div[contains(@class,"col-span-full")]')

        # --- NIP ---
        self._input_tax_id = self.find('#taxIdentificationNumber')

        # --- dane firmy (auto-uzupełniane po NIP) ---
        self._input_company_name = self.find('#companyName')
        self._input_street_name = self.find('#streetName')
        self._input_street_number = self.find('#streetNumber')
        self._input_postal_code = self.find('#postalCode')
        self._input_city = self.find('#city')

        # --- kontakt ---
        self._input_phone = self.find('#phoneNumber')
        self._input_business_email = self.find('#email')

    # ============================================================
    # ACTIONS
    # ============================================================

    def fill_login(self, email: str) -> "RegisterPage":
        self.safe_fill(self._input_login, email)
        return self

    def fill_password(self, password: str) -> "RegisterPage":
        self.safe_fill(self._input_password, password)
        return self

    def fill_repeated_password(self, password: str) -> "RegisterPage":
        self.safe_fill(self._input_password_repeated, password)
        return self

    def check_business_offer(self) -> "RegisterPage":
        self.safe_click(self._checkbox_business_offer)
        expect(self._input_tax_id).to_be_visible()
        return self

    def accept_required_terms(self) -> "RegisterPage":
        self.safe_click(self._checkbox_terms)
        return self

    def accept_marketing_terms(self) -> "RegisterPage":
        self.safe_click(self._checkbox_marketing)
        return self

    def submit_registration(self) -> None:
        self.safe_click(self._button_register)

    def go_to_login(self) -> None:
        self.safe_click(self._button_login_redirect)

    def fill_business_personal_data(self, nip: str, phone: str, email: str) -> "RegisterClient":
        expect(self._input_tax_id).to_be_enabled()
        self._input_tax_id.fill(nip)
        expect(self._input_phone).to_be_enabled()
        self._input_phone.fill(phone)
        expect(self._input_business_email).to_be_enabled()
        self._input_business_email.fill(email)
        return self

    def solve_captcha(self) -> "RegisterClient":
        frame = self.root.page.frame_locator('#recaptcha-register iframe[title="reCAPTCHA"]')
        checkbox = frame.locator('#recaptcha-anchor')
        checkbox.click(timeout=10000)
        return self
