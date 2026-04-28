from __future__ import annotations

import time
from typing import Self

from playwright.sync_api import Locator, Page, expect

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
        self._city_input = self.find("#city")
        self._city_select_input_area = self.find("css=div[data-role='selectInputArea']")
        self._city_select_options_container = self.find("[data-name='selectOptions']")
        self._country_name_input = self.find("#countryName")

        self._phone_number_input = self.find("#phoneNumber")
        self._email_input = self.find("#email")

        self._cancel_button = self.find("role=button[name='Anuluj']")
        self._add_details_button = self.find("role=button[name='Dodaj dane']")

        self._copy_data_from_receiver_checkbox = self.find("#copyDataFromReceiver")
        self._tax_identification_number_input = self.find("#taxIdentificationNumber")

    def _click_private_person(self) -> Self:
        self.pointer_click(self._private_person_button).sleep(1_000)
        return self

    def _click_company(self) -> Self:
        self.pointer_click(self._company_button).sleep(1_000)
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
        self.safe_type(self._postal_code_input, value).sleep(1_500)
        return self

    def _is_city_input_mode(self) -> bool:
        """Check if city field is an input (company/GUS mode) or select (private person mode)."""
        return _is_visible(self._city_input)

    def _enter_city_via_select(self, value: str) -> Self:
        self.sleep(1_500)
        self.pointer_click(self._city_select_input_area)
        expect(self._city_select_options_container).to_be_visible(timeout=5_000)
        option = self._city_select_options_container.get_by_text(value, exact=True).first
        expect(option).to_be_visible(timeout=self.DEFAULT_TIMEOUT)
        self.pointer_click(option, timeout=1_500)
        return self

    def _enter_city(self, value: str) -> Self:
        if self._is_city_input_mode():
            if not self._city_input.first.is_disabled():
                self.safe_type(self._city_input, value)
        else:
            self._enter_city_via_select(value)
        return self

    def _enter_phone_number(self, value: str) -> Self:
        self.safe_fill(self._phone_number_input, value)
        return self

    def _enter_email(self, value: str) -> Self:
        self.safe_fill(self._email_input, value)
        return self

    def _click_cancel(self) -> None:
        self.pointer_click(self._cancel_button)

    def _click_add_details(self) -> None:
        self.pointer_click(self._add_details_button)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split()).casefold()

    def _input_is_empty(self, locator: Locator) -> bool:
        raw = (locator.first.input_value() or "").strip()
        return raw == ""

    def _fill_input_if_missing(self, locator: Locator, value: str, *, use_fill: bool = False) -> Self:
        if value and self._input_is_empty(locator):
            if use_fill:
                self.safe_fill(locator, value)
            else:
                self.safe_type(locator, value)
        return self

    def _is_city_selected(self, value: str) -> bool:
        if self._is_city_input_mode():
            current = (self._city_input.first.input_value() or "").strip()
        else:
            current = (self._city_select_input_area.first.inner_text() or "").strip()
        return self._normalize_text(current) == self._normalize_text(value)

    def _is_city_empty(self) -> bool:
        if self._is_city_input_mode():
            current = (self._city_input.first.input_value() or "").strip()
        else:
            current = (self._city_select_input_area.first.inner_text() or "").strip()
        return current == ""

    def _enter_city_if_missing(self, value: str) -> Self:
        if value and not self._is_city_selected(value):
            self._enter_city(value)
        return self

    def _has_company_data_from_gus(self) -> bool:
        has_any_input_filled = any(
            not self._input_is_empty(locator)
            for locator in (
                self._company_name_input,
                self._street_name_input,
                self._street_number_input,
                self._postal_code_input,
                self._city_input,
            )
        )
        return has_any_input_filled

    @step("Czekam na dane firmy z GUS")
    def _wait_for_gus_company_data(self, timeout_ms: int = 5_000) -> Self:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            if self._has_company_data_from_gus():
                break
            self.sleep(200)
        return self

    @step("Wypelniam brakujace dane osobowe")
    def _fill_common_person_data_if_missing(
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
        self._fill_input_if_missing(self._first_name_input, first_name)
        self._fill_input_if_missing(self._surname_input, surname)
        self._fill_input_if_missing(self._street_name_input, street_name)
        self._fill_input_if_missing(self._street_number_input, street_number)
        self._fill_input_if_missing(self._postal_code_input, postal_code)
        self._enter_city_if_missing(city)
        self._fill_input_if_missing(self._phone_number_input, phone_number, use_fill=True)
        self._fill_input_if_missing(self._email_input, email, use_fill=True)
        return self

    @step("Wypelniam brakujace dane adresowe firmy")
    def _fill_company_address_data_if_missing(
        self,
        *,
        street_name: str,
        street_number: str,
        postal_code: str,
        city: str,
        phone_number: str,
        email: str,
    ) -> Self:
        self._fill_input_if_missing(self._street_name_input, street_name)
        self._fill_input_if_missing(self._street_number_input, street_number)
        self._fill_input_if_missing(self._postal_code_input, postal_code)
        self._enter_city_if_missing(city)
        self._fill_input_if_missing(self._phone_number_input, phone_number, use_fill=True)
        self._fill_input_if_missing(self._email_input, email, use_fill=True)
        return self

    @step("Wypelniam dane osobowe")
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
            self.pointer_click(checkbox)
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
            self.enter_tax_identification_number(data.tax_identification_number or "")
            self._wait_for_gus_company_data(timeout_ms=5_000)

            company_name = data.company_name or f"{data.first_name} {data.surname}"
            self._fill_input_if_missing(self._company_name_input, company_name)
        else:
            self.click_private_person()

        copy_from_receiver_enabled = data.copy_data_from_receiver and _is_visible(
            self._copy_data_from_receiver_checkbox
        )
        self.set_copy_data_from_receiver(copy_from_receiver_enabled)

        if not copy_from_receiver_enabled:
            if data.is_company:
                self._fill_company_address_data_if_missing(
                    street_name=data.street_name,
                    street_number=data.street_number,
                    postal_code=data.postal_code,
                    city=data.city,
                    phone_number=data.phone_number,
                    email=data.email,
                )
            else:
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
