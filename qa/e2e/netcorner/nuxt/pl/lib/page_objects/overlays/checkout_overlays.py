from __future__ import annotations

import re
from typing import Self

from playwright.sync_api import Locator, Page, expect

from framework.base.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    CheckoutPurchaserData,
    DeliveryCourierReceiverData,
)


def _is_visible(locator: Locator) -> bool:
    target = locator.first
    return target.count() > 0 and target.is_visible()


class DeliveryCourierRecieverOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(
            page.locator('[data-name="OrderAddressDialog"]:visible').filter(
                has=page.get_by_role(
                    "heading",
                    name=re.compile(r"Dodaj dane do dostawy|Delivery Courier Receiver Overlay", re.IGNORECASE),
                )
            ),
            name="Delivery Courier Receiver Overlay",
        )

        self.__private_person_button = self.find("role=button[name='Osoba prywatna']")
        self.__company_button = self.find("role=button[name='Firma']")

        self.__first_name_input = self.find("#firstName")
        self.__surname_input = self.find("#surname")
        self.__company_name_input = self.find("#companyName")
        self.__street_name_input = self.find("#streetName")
        self.__street_number_input = self.find("#streetNumber")
        self.__postal_code_input = self.find("#postalCode")
        self.__city_select_input_area = self.find("css=div[data-role='selectInputArea']")
        self.__city_select_label = self.find("css=div[data-role='selectLabel']")

        self.__phone_number_input = self.find("#phoneNumber")
        self.__email_input = self.find("#email")

        self.__cancel_button = self.find("role=button[name='Anuluj']")
        self.__add_details_button = self.find("role=button[name='Dodaj dane']")

    @step("Klikam 'Osoba prywatna'")
    def click_private_person(self) -> None:
        self.safe_click(self.__private_person_button)

    @step("Klikam 'Firma'")
    def click_company(self) -> None:
        self.safe_click(self.__company_button)

    @step("Wpisuję imię {value}")
    def enter_first_name(self, value: str) -> None:
        self.safe_type(self.__first_name_input, value)

    @step("Wpisuję nazwisko {value}")
    def enter_surname(self, value: str) -> None:
        self.safe_type(self.__surname_input, value)

    @step("Wpisuję nazwę firmy {value}")
    def enter_company_name(self, value: str) -> None:
        self.safe_type(self.__company_name_input, value)

    @step("Wpisuję ulicę {value}")
    def enter_street_name(self, value: str) -> None:
        self.safe_type(self.__street_name_input, value)

    @step("Wpisuję numer domu/lokalu {value}")
    def enter_street_number(self, value: str) -> None:
        self.safe_type(self.__street_number_input, value)

    @step("Wpisuję kod pocztowy {value}")
    def enter_postal_code(self, value: str) -> None:
        self.safe_type(self.__postal_code_input, value)

    @step("Wybieram miejscowość {value}")
    def enter_city(self, value: str) -> None:
        self.safe_click(self.__city_select_input_area)
        self.root.page.keyboard.type(value)
        self.root.page.keyboard.press("Enter")
        try:
            expect(self.__city_select_label).to_contain_text(value, timeout=3_000)
        except Exception:
            self.safe_click(self.root.get_by_text(value, exact=False).first)
            expect(self.__city_select_label).to_contain_text(value, timeout=self.DEFAULT_TIMEOUT)

    @step("Wpisuję numer telefonu {value}")
    def enter_phone_number(self, value: str) -> None:
        self.safe_type(self.__phone_number_input, value)

    @step("Wpisuję e-mail {value}")
    def enter_email(self, value: str) -> None:
        self.safe_type(self.__email_input, value)

    @step("Klikam 'Anuluj'")
    def click_cancel(self) -> None:
        self.safe_click(self.__cancel_button)

    @step("Klikam 'Dodaj dane'")
    def click_add_details(self) -> None:
        self.safe_click(self.__add_details_button)

    @step("Wypełniam dane odbiorcy kuriera")
    def fill_receiver_data(self, data: DeliveryCourierReceiverData) -> None:
        if data.is_company:
            self.click_company()
            company_name = data.company_name or f"{data.first_name} {data.surname}"
            self.enter_company_name(company_name)
        else:
            self.click_private_person()

        self.enter_first_name(data.first_name)
        self.enter_surname(data.surname)
        self.enter_street_name(data.street_name)
        self.enter_street_number(data.street_number)
        self.enter_postal_code(data.postal_code)
        self.enter_city(data.city)
        self.enter_phone_number(data.phone_number)
        self.enter_email(data.email)


class CheckoutPurchaserOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(
            page.locator('[data-name="OrderAddressDialog"]:visible').filter(
                has=page.get_by_role(
                    "heading",
                    name=re.compile(r"Podaj dane do zakupu|Checkout Purchaser Overlay", re.IGNORECASE),
                )
            ),
            name="Checkout Purchaser Overlay",
        )

        self.__private_person_button = self.find("role=button[name='Osoba prywatna']")
        self.__company_button = self.find("role=button[name='Firma']")
        self.__copy_data_from_receiver_checkbox = self.find("#copyDataFromReceiver")

        self.__first_name_input = self.find("#firstName")
        self.__surname_input = self.find("#surname")
        self.__company_name_input = self.find("#companyName")
        self.__tax_identification_number_input = self.find("#taxIdentificationNumber")
        self.__street_name_input = self.find("#streetName")
        self.__street_number_input = self.find("#streetNumber")
        self.__postal_code_input = self.find("#postalCode")
        self.__city_select_input_area = self.find("css=div[data-role='selectInputArea']")
        self.__city_select_label = self.find("css=div[data-role='selectLabel']")
        self.__phone_number_input = self.find("#phoneNumber")
        self.__email_input = self.find("#email")

        self.__cancel_button = self.find("role=button[name='Anuluj']")
        self.__add_details_button = self.find("role=button[name='Dodaj dane']")

    @step("Klikam 'Osoba prywatna' (kupujacy)")
    def click_private_person(self) -> None:
        self.safe_click(self.__private_person_button)

    @step("Klikam 'Firma' (kupujacy)")
    def click_company(self) -> None:
        self.safe_click(self.__company_button)

    @step("Ustawiam 'Skopiuj dane odbiorcy' na {enabled}")
    def set_copy_data_from_receiver(self, enabled: bool) -> None:
        if not _is_visible(self.__copy_data_from_receiver_checkbox):
            return

        checkbox = self.__copy_data_from_receiver_checkbox.first
        if checkbox.is_checked() != enabled:
            self.safe_click(checkbox)

    @step("Wpisuje imie kupujacego {value}")
    def enter_first_name(self, value: str) -> None:
        self.safe_type(self.__first_name_input, value)

    @step("Wpisuje nazwisko kupujacego {value}")
    def enter_surname(self, value: str) -> None:
        self.safe_type(self.__surname_input, value)

    @step("Wpisuje nazwe firmy kupujacego {value}")
    def enter_company_name(self, value: str) -> None:
        self.safe_type(self.__company_name_input, value)

    @step("Wpisuje NIP kupujacego {value}")
    def enter_tax_identification_number(self, value: str) -> None:
        if _is_visible(self.__tax_identification_number_input):
            self.safe_type(self.__tax_identification_number_input, value)

    @step("Wpisuje ulice kupujacego {value}")
    def enter_street_name(self, value: str) -> None:
        self.safe_type(self.__street_name_input, value)

    @step("Wpisuje numer domu/lokalu kupujacego {value}")
    def enter_street_number(self, value: str) -> None:
        self.safe_type(self.__street_number_input, value)

    @step("Wpisuje kod pocztowy kupujacego {value}")
    def enter_postal_code(self, value: str) -> None:
        self.safe_type(self.__postal_code_input, value)

    @step("Wybieram miejscowosc kupujacego {value}")
    def enter_city(self, value: str) -> None:
        self.safe_click(self.__city_select_input_area)
        self.root.page.keyboard.type(value)
        self.root.page.keyboard.press("Enter")
        try:
            expect(self.__city_select_label).to_contain_text(value, timeout=3_000)
        except Exception:
            self.safe_click(self.root.get_by_text(value, exact=False).first)
            expect(self.__city_select_label).to_contain_text(value, timeout=self.DEFAULT_TIMEOUT)

    @step("Wpisuje numer telefonu kupujacego {value}")
    def enter_phone_number(self, value: str) -> None:
        self.safe_type(self.__phone_number_input, value)

    @step("Wpisuje e-mail kupujacego {value}")
    def enter_email(self, value: str) -> None:
        self.safe_type(self.__email_input, value)

    @step("Klikam 'Anuluj' (kupujacy)")
    def click_cancel(self) -> None:
        self.safe_click(self.__cancel_button)

    @step("Klikam 'Dodaj dane' (kupujacy)")
    def click_add_details(self) -> None:
        self.safe_click(self.__add_details_button)

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

        copy_from_receiver_enabled = data.copy_data_from_receiver and _is_visible(self.__copy_data_from_receiver_checkbox)
        self.set_copy_data_from_receiver(copy_from_receiver_enabled)

        if not copy_from_receiver_enabled:
            self.enter_first_name(data.first_name)
            self.enter_surname(data.surname)
            self.enter_street_name(data.street_name)
            self.enter_street_number(data.street_number)
            self.enter_postal_code(data.postal_code)
            self.enter_city(data.city)
            self.enter_phone_number(data.phone_number)
            self.enter_email(data.email)

        return self
