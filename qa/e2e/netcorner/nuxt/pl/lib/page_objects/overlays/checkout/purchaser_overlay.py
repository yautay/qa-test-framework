from __future__ import annotations

from typing import Self

from playwright.sync_api import Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import CheckoutPurchaserData

from .common import _is_visible, _order_address_dialog_root


class CheckoutPurchaserOverlay(BaseComponent):
    def __init__(self, page: Page):
        root = _order_address_dialog_root(page, r"Podaj dane do zakupu|Checkout Purchaser Overlay")
        super().__init__(
            root,
            name="Checkout Purchaser Overlay",
        )

        self._private_person_button = self.find("role=button[name='Osoba prywatna']")
        self._company_button = self.find("role=button[name='Firma']")

        self._first_name_input = self.find("#firstName")
        self._surname_input = self.find("#surname")
        self._company_name_input = self.find("#companyName")
        self._street_name_input = self.find("#streetName")
        self._street_number_input = self.find("#streetNumber")
        self._postal_code_input = self.find("#postalCode")
        self._city_select_input_area = self.find("css=div[data-role='selectInputArea']")
        self._city_select_options_container = self.find("[data-name='selectOptions']")

        self._phone_number_input = self.find("#phoneNumber")
        self._email_input = self.find("#email")

        self._cancel_button = self.find("role=button[name='Anuluj']")
        self._add_details_button = self.find("role=button[name='Dodaj dane']")

        self._copy_data_from_receiver_checkbox = self.find("#copyDataFromReceiver")
        self._tax_identification_number_input = self.find("#taxIdentificationNumber")

    def _click_private_person(self) -> Self:
        self.safe_click(self._private_person_button)
        return self

    def _click_company(self) -> Self:
        self.safe_click(self._company_button)
        return self

    def _enter_first_name(self, value: str) -> Self:
        self.safe_type(self._first_name_input, value)
        return self

    def _enter_surname(self, value: str) -> Self:
        self.safe_type(self._surname_input, value)
        return self

    def _enter_company_name(self, value: str) -> Self:
        self.safe_type(self._company_name_input, value)
        return self

    def _enter_street_name(self, value: str) -> Self:
        self.safe_type(self._street_name_input, value)
        return self

    def _enter_street_number(self, value: str) -> Self:
        self.safe_type(self._street_number_input, value)
        return self

    def _enter_postal_code(self, value: str) -> Self:
        self.safe_type(self._postal_code_input, value)
        return self

    def _enter_city(self, value: str) -> Self:
        self.sleep(1_500)
        self.safe_click(self._city_select_input_area)
        expect(self._city_select_options_container).to_be_visible(timeout=5_000)
        option = self._city_select_options_container.get_by_text(value, exact=True).first
        if option.count() == 0:
            option = self._city_select_options_container.locator("div", has_text=value).first
        if option.count() == 0:
            raise AssertionError(f"Nie znaleziono opcji selekta o tekście: {value!r}")
        expect(option).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        option.scroll_into_view_if_needed()
        option.click(timeout=self.DEFAULT_TIMEOUT)
        return self

    def _enter_phone_number(self, value: str) -> Self:
        self.safe_fill(self._phone_number_input, value)
        return self

    def _enter_email(self, value: str) -> Self:
        self.safe_fill(self._email_input, value)
        return self

    def _click_cancel(self) -> None:
        self.safe_click(self._cancel_button)

    def _click_add_details(self) -> None:
        self.safe_click(self._add_details_button)

    def _fill_common_person_data(
        self,
        *,
        first_name: str,
        surname: str,
        street_name: str,
        street_number: str,
        postal_code: str,
        city: str,
        phone_number: str,
        email: str,
    ) -> Self:
        self._enter_first_name(first_name)
        self._enter_surname(surname)
        self._enter_street_name(street_name)
        self._enter_street_number(street_number)
        self._enter_postal_code(postal_code)
        self._enter_city(city)
        self._enter_phone_number(phone_number)
        self._enter_email(email)
        return self

    @step("Klikam 'Osoba prywatna' (kupujacy)")
    def click_private_person(self) -> Self:
        return self._click_private_person()

    @step("Klikam 'Firma' (kupujacy)")
    def click_company(self) -> Self:
        return self._click_company()

    @step("Ustawiam 'Skopiuj dane odbiorcy' na {enabled}")
    def set_copy_data_from_receiver(self, enabled: bool) -> Self:
        if not _is_visible(self._copy_data_from_receiver_checkbox):
            return self

        checkbox = self._copy_data_from_receiver_checkbox.first
        if checkbox.is_checked() != enabled:
            self.safe_click(checkbox)
        return self

    @step("Wpisuje imie kupujacego {value}")
    def enter_first_name(self, value: str) -> Self:
        return self._enter_first_name(value)

    @step("Wpisuje nazwisko kupujacego {value}")
    def enter_surname(self, value: str) -> Self:
        return self._enter_surname(value)

    @step("Wpisuje nazwe firmy kupujacego {value}")
    def enter_company_name(self, value: str) -> Self:
        return self._enter_company_name(value)

    @step("Wpisuje NIP kupujacego {value}")
    def enter_tax_identification_number(self, value: str) -> Self:
        if _is_visible(self._tax_identification_number_input):
            self.safe_type(self._tax_identification_number_input, value)
        return self

    @step("Wpisuje ulice kupujacego {value}")
    def enter_street_name(self, value: str) -> Self:
        return self._enter_street_name(value)

    @step("Wpisuje numer domu/lokalu kupujacego {value}")
    def enter_street_number(self, value: str) -> Self:
        return self._enter_street_number(value)

    @step("Wpisuje kod pocztowy kupujacego {value}")
    def enter_postal_code(self, value: str) -> Self:
        return self._enter_postal_code(value)

    @step("Wybieram miejscowosc kupujacego {value}")
    def enter_city(self, value: str) -> Self:
        return self._enter_city(value)

    @step("Wpisuje numer telefonu kupujacego {value}")
    def enter_phone_number(self, value: str) -> Self:
        return self._enter_phone_number(value)

    @step("Wpisuje e-mail kupujacego {value}")
    def enter_email(self, value: str) -> Self:
        return self._enter_email(value)

    @step("Klikam 'Anuluj' (kupujacy)")
    def click_cancel(self) -> None:
        self._click_cancel()

    @step("Klikam 'Dodaj dane' (kupujacy)")
    def click_add_details(self) -> None:
        self._click_add_details()

    @step("Wypelniam dane kupujacego")
    def fill_purchaser_data(
        self,
        data: CheckoutPurchaserData,
    ) -> Self:
        if data.is_company:
            self.click_company()
            company_name = data.company_name or f"{data.first_name} {data.surname}"
            self.enter_company_name(company_name)
            self.enter_tax_identification_number(data.tax_identification_number or "")
        else:
            self.click_private_person()

        copy_from_receiver_enabled = data.copy_data_from_receiver and _is_visible(
            self._copy_data_from_receiver_checkbox
        )
        self.set_copy_data_from_receiver(copy_from_receiver_enabled)

        if not copy_from_receiver_enabled:
            self._fill_common_person_data(
                first_name=data.first_name,
                surname=data.surname,
                street_name=data.street_name,
                street_number=data.street_number,
                postal_code=data.postal_code,
                city=data.city,
                phone_number=data.phone_number,
                email=data.email,
            )

        return self
