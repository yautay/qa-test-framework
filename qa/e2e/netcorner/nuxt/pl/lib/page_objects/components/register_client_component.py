from __future__ import annotations

from playwright.sync_api import expect, Locator
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class RegisterClientComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Register Client Component")

        self.__input_login = self.find("#login")
        self.__input_password = self.find("#password")
        self.__input_password_repeated = self.find("#passwordRepeated")

        self.__checkbox_business_offer = self.find("#businessOffer")
        self.__checkbox_terms = self.find("#customer_company_rules_terms")
        self.__checkbox_marketing = self.find("#customer_marketing_terms")

        self.__recaptcha_container = self.find("#recaptcha-register")

        self.__button_register = self.find('button:has-text("Załóż konto")')
        self.__button_login_redirect = self.find('button:has-text("Masz już konto? Zaloguj się.")')

        self.__business_section = self.find("#businessOffer").locator(
            'xpath=ancestor::div[contains(@class,"col-span-full")]'
        )

        # --- NIP ---
        self.__input_tax_id = self.find("#taxIdentificationNumber")

        # --- dane firmy (auto-uzupełniane po NIP) ---
        self.__input_company_name = self.find("#companyName")
        self.__input_street_name = self.find("#streetName")
        self.__input_street_number = self.find("#streetNumber")
        self.__input_postal_code = self.find("#postalCode")
        self.__input_city = self.find("#city")

        # --- kontakt ---
        self.__input_phone = self.find("#phoneNumber")
        self.__input_business_email = self.find("#email")

    # ============================================================
    # ACTIONS
    # ============================================================

    @step("Wpisuję login klienta: {email}")
    def fill_login(self, email: str) -> "RegisterClientComponent":
        self.safe_type(self.__input_login, email)
        return self

    @step("Ustawiam hasło klienta: {password}")
    def fill_password(self, password: str) -> "RegisterClientComponent":
        self.safe_type(self.__input_password, password)
        return self

    @step("Powtarzam hasło: {password}")
    def fill_repeated_password(self, password: str) -> "RegisterClientComponent":
        self.safe_type(self.__input_password_repeated, password)
        return self

    @step("Aktywuję ofertę biznesową i sprawdzam pola NIP")
    def check_business_offer(self) -> "RegisterClientComponent":
        self.safe_click(self.__checkbox_business_offer)
        expect(self.__input_tax_id).to_be_visible()
        return self

    @step("Akceptuję obowiązkowe regulaminy")
    def accept_required_terms(self) -> "RegisterClientComponent":
        self.safe_click(self.__checkbox_terms)
        return self

    @step("Akceptuję zgody marketingowe")
    def accept_marketing_terms(self) -> "RegisterClientComponent":
        self.safe_click(self.__checkbox_marketing)
        return self

    @step("Klikam przycisk 'Załóż konto'")
    def submit_registration(self) -> None:
        self.safe_click(self.__button_register)

    @step("Przechodzę do ekranu logowania")
    def go_to_login(self) -> None:
        self.safe_click(self.__button_login_redirect)

    @step("Wpisuję dane firmowe NIP={nip}, tel={phone}, email={email}")
    def fill_business_personal_data(self, nip: str, phone: str, email: str) -> "RegisterClientComponent":
        self.safe_type(self.__input_tax_id, nip)
        self.safe_type(self.__input_phone, phone)
        self.safe_type(self.__input_business_email, email)
        return self

    @step("Klikam reCAPTCHA, by potwierdzić, że nie jestem botem")
    def solve_captcha(self) -> "RegisterClientComponent":
        frame = self.root.page.frame_locator('#recaptcha-register iframe[title="reCAPTCHA"]')
        checkbox = frame.locator("#recaptcha-anchor")
        expect(checkbox).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        checkbox.click(timeout=self.DEFAULT_TIMEOUT)
        return self
