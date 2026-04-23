from __future__ import annotations

import random
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    CheckoutPurchaserData,
    DeliveryCourierReceiverData,
)


def _is_visible(locator: Locator) -> bool:
    target = locator.first
    return target.count() > 0 and target.is_visible()


@dataclass(frozen=True, slots=True)
class StorehouseData:
    data_id: str
    name: str


def _order_address_dialog_root(page: Page, heading_pattern: str) -> Locator:
    return page.locator('[data-name="OrderAddressDialog"]:visible').filter(
        has=page.get_by_role("heading", name=re.compile(heading_pattern, re.IGNORECASE))
    )


class DeliveryCourierReceiverOverlay(BaseComponent):
    def __init__(self, page: Page):
        root = _order_address_dialog_root(page, r"Dodaj dane do dostawy|Delivery Courier Receiver Overlay")
        super().__init__(
            root,
            name="Delivery Courier Receiver Overlay",
        )

        self._private_person_button = self.find("role=button[name='Osoba prywatna']")
        self._company_button = self.find("role=button[name='Firma']")

        self._first_name_input = self.find("#firstName")
        self._surname_input = self.find("#surname")
        self._company_name_input = self.find("#companyName")
        self._street_name_input = self.find("#streetName")
        self._street_number_input = self.find("#streetNumber")
        self._postal_code_input = self.find("#postalCode")
        self._city_select_input_area = self.find("[data-role='selectInputArea']")
        self._city_select_options_container = self.find("[data-name='selectOptions']")

        self._phone_number_input = self.find("#phoneNumber")
        self._email_input = self.find("#email")

        self._cancel_button = self.find("role=button[name='Anuluj']")
        self._add_details_button = self.find("role=button[name='Dodaj dane']")

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

    @step("Klikam 'Osoba prywatna'")
    def click_private_person(self) -> Self:
        return self._click_private_person()

    @step("Klikam 'Firma'")
    def click_company(self) -> Self:
        return self._click_company()

    @step("Wpisuję imię {value}")
    def enter_first_name(self, value: str) -> Self:
        return self._enter_first_name(value)

    @step("Wpisuję nazwisko {value}")
    def enter_surname(self, value: str) -> Self:
        return self._enter_surname(value)

    @step("Wpisuję nazwę firmy {value}")
    def enter_company_name(self, value: str) -> Self:
        return self._enter_company_name(value)

    @step("Wpisuję ulicę {value}")
    def enter_street_name(self, value: str) -> Self:
        return self._enter_street_name(value)

    @step("Wpisuję numer domu/lokalu {value}")
    def enter_street_number(self, value: str) -> Self:
        return self._enter_street_number(value)

    @step("Wpisuję kod pocztowy {value}")
    def enter_postal_code(self, value: str) -> Self:
        return self._enter_postal_code(value)

    @step("Wybieram miejscowość {value}")
    def enter_city(self, value: str) -> Self:
        return self._enter_city(value)

    @step("Wpisuję numer telefonu {value}")
    def enter_phone_number(self, value: str) -> Self:
        return self._enter_phone_number(value)

    @step("Wpisuję e-mail {value}")
    def enter_email(self, value: str) -> Self:
        return self._enter_email(value)

    @step("Klikam 'Anuluj'")
    def click_cancel(self) -> None:
        self._click_cancel()

    @step("Klikam 'Dodaj dane'")
    def click_add_details(self) -> None:
        self._click_add_details()

    @step("Wypełniam dane odbiorcy kuriera")
    def fill_receiver_data(self, data: DeliveryCourierReceiverData) -> Self:
        if data.is_company:
            self.click_company()
            company_name = data.company_name or f"{data.first_name} {data.surname}"
            self.enter_company_name(company_name)
        else:
            self.click_private_person()

        return self._fill_common_person_data(
            first_name=data.first_name,
            surname=data.surname,
            street_name=data.street_name,
            street_number=data.street_number,
            postal_code=data.postal_code,
            city=data.city,
            phone_number=data.phone_number,
            email=data.email,
        )


class DeliveryStorehouseReceiverOverlay(BaseComponent):
    ROOT_SELECTOR = 'div[data-name="orderMap"]'
    MAP_SETTLE_TIMEOUT_MS = 2_000
    MAX_STABLE_ZOOM_ITERATIONS = 5

    def __init__(self, scope: Page | Locator) -> None:
        root = self.resolve_root(scope, self.ROOT_SELECTOR)
        super().__init__(root, name="Delivery Storehouse Receiver Overlay")

        self.__visit_us_input = self.find("#visitUs")
        self.__search_button = self.find('[data-name="searchInput"] button:has(i.i-search)')
        self.__parcel_list = self.find('[data-name="parcelList"]')
        self.__storehouse_tiles = self.__parcel_list.locator('[data-name="orderPickerTile"]')
        self.__zoom_in_button = self.find('[aria-label="Zoom in"]')
        self.__zoom_out_button = self.find('[aria-label="Zoom out"]')

    @staticmethod
    def __normalize_text(value: str) -> str:
        return " ".join(value.split())

    def __wait_for_storehouses(self, timeout: int | None = None) -> None:
        expect(self.__parcel_list).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        expect(self.__storehouse_tiles.first).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        self.root.page.wait_for_timeout(self.MAP_SETTLE_TIMEOUT_MS)

    def __visible_storehouse_tiles(self) -> list[Locator]:
        visible_tiles: list[Locator] = []
        for index in range(self.__storehouse_tiles.count()):
            tile = self.__storehouse_tiles.nth(index)
            if tile.is_visible():
                visible_tiles.append(tile)
        return visible_tiles

    def __read_storehouse_data(self, tile: Locator) -> StorehouseData | None:
        data_id = (tile.get_attribute("data-id") or "").strip()
        if not data_id:
            return None

        name_locator = tile.locator("div.flex.items-start p[title]").first
        if name_locator.count() == 0:
            name_locator = tile.locator("p[title]").first

        name = ""
        if name_locator.count() > 0:
            name = self.__normalize_text((name_locator.text_content() or "").strip())

        if not name:
            fallback_text = self.__normalize_text((tile.text_content() or "").strip())
            if fallback_text:
                name = fallback_text.split("Otwarte:", 1)[0].strip()

        if not name:
            return None

        return StorehouseData(data_id=data_id, name=name)

    def __is_zoom_button_enabled(self, button: Locator) -> bool:
        target = button.first
        if target.count() == 0 or not target.is_visible():
            return False
        return (target.get_attribute("aria-disabled") or "").strip().lower() != "true"

    def __click_zoom_button(self, button: Locator) -> bool:
        if not self.__is_zoom_button_enabled(button):
            return False
        self.safe_click(button)
        self.root.page.wait_for_timeout(self.MAP_SETTLE_TIMEOUT_MS)
        return True

    def __zoom_out(self) -> bool:
        return self.__click_zoom_button(self.__zoom_out_button)

    def __zoom_in(self) -> bool:
        return self.__click_zoom_button(self.__zoom_in_button)

    def __collect_visible_storehouses(self) -> list[StorehouseData]:
        unique_by_id: dict[str, StorehouseData] = {}
        for tile in self.__visible_storehouse_tiles():
            storehouse_data = self.__read_storehouse_data(tile)
            if storehouse_data is None:
                continue
            unique_by_id[storehouse_data.data_id] = storehouse_data
        return list(unique_by_id.values())

    def __collect_storehouses_with_zoom(self, max_zoom_iterations: int = 4) -> list[StorehouseData]:
        self.__wait_for_storehouses()

        unique_by_id: dict[str, StorehouseData] = {
            storehouse.data_id: storehouse for storehouse in self.__collect_visible_storehouses()
        }
        stable_zoom_iterations = 0

        for _ in range(max(0, max_zoom_iterations)):
            before_count = len(unique_by_id)
            zoom_changed = self.__zoom_out()
            if not zoom_changed:
                zoom_changed = self.__zoom_in()
            if not zoom_changed:
                break

            for storehouse in self.__collect_visible_storehouses():
                unique_by_id[storehouse.data_id] = storehouse

            if len(unique_by_id) == before_count:
                stable_zoom_iterations += 1
                if stable_zoom_iterations >= self.MAX_STABLE_ZOOM_ITERATIONS:
                    break
                if self.__zoom_in() and self.__zoom_out():
                    for storehouse in self.__collect_visible_storehouses():
                        unique_by_id[storehouse.data_id] = storehouse
                    if len(unique_by_id) > before_count:
                        stable_zoom_iterations = 0
            else:
                stable_zoom_iterations = 0

        return list(unique_by_id.values())

    def __choose_storehouse(
        self,
        matcher: Callable[[StorehouseData], bool],
        max_zoom_iterations: int = 4,
    ) -> StorehouseData:
        self.__wait_for_storehouses()
        for zoom_iteration in range(max(0, max_zoom_iterations) + 1):
            for tile in self.__visible_storehouse_tiles():
                storehouse_data = self.__read_storehouse_data(tile)
                if storehouse_data is None or not matcher(storehouse_data):
                    continue
                self.safe_click(tile)
                return storehouse_data

            if zoom_iteration == max(0, max_zoom_iterations):
                break

            if not self.__zoom_out() and not self.__zoom_in():
                break

        raise RuntimeError("Nie znaleziono salonu spełniającego kryteria wyboru.")

    @step("Uzupełniam kod pocztowy lub miasto: {value}")
    def fill_visit_us(self, value: str) -> Self:
        self.safe_fill(self.__visit_us_input, value)
        return self

    @step("Klikam ikonę wyszukiwania")
    def click_search_icon(self) -> Self:
        self.safe_click(self.__search_button)
        return self

    @step("Wyszukuję salony dla lokalizacji: {value}")
    def search_storehouses(self, value: str, max_zoom_iterations: int = 4) -> list[StorehouseData]:
        self.fill_visit_us(value)
        self.click_search_icon()
        return self.get_available_storehouses(max_zoom_iterations=max_zoom_iterations)

    @step("Pobieram listę dostępnych salonów")
    def get_available_storehouses(self, max_zoom_iterations: int = 4) -> list[StorehouseData]:
        return self.__collect_storehouses_with_zoom(max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram salon o nazwie: {storehouse_name}")
    def choose_storehouse_by_name(self, storehouse_name: str, max_zoom_iterations: int = 4) -> StorehouseData:
        normalized_target = self.__normalize_text(storehouse_name).casefold()
        if not normalized_target:
            raise ValueError("Nazwa salonu nie może być pusta.")

        def matcher(storehouse: StorehouseData) -> bool:
            normalized_name = self.__normalize_text(storehouse.name).casefold()
            return normalized_target in normalized_name

        return self.__choose_storehouse(matcher, max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram salon o data-id: {storehouse_data_id}")
    def choose_storehouse_by_data_id(self, storehouse_data_id: str, max_zoom_iterations: int = 4) -> StorehouseData:
        normalized_target = storehouse_data_id.strip()
        if not normalized_target:
            raise ValueError("data-id salonu nie może być puste.")

        return self.__choose_storehouse(
            lambda storehouse: storehouse.data_id == normalized_target,
            max_zoom_iterations=max_zoom_iterations,
        )

    @step("Wybieram losowy salon")
    def choose_random_storehouse(self, max_zoom_iterations: int = 4) -> StorehouseData:
        available_storehouses = self.get_available_storehouses(max_zoom_iterations=max_zoom_iterations)
        if not available_storehouses:
            raise RuntimeError("Brak dostępnych salonów do wyboru.")

        selected_storehouse = random.choice(available_storehouses)
        return self.choose_storehouse_by_data_id(
            selected_storehouse.data_id,
            max_zoom_iterations=max_zoom_iterations,
        )


class DeliveryDhlPopReceiverOverlay(DeliveryStorehouseReceiverOverlay):
    OVERLAY_NAME = "Delivery DHL POP Receiver Overlay"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope)
        self.name = self.OVERLAY_NAME

    @step("Wyszukuję punkty DHL POP dla lokalizacji: {value}")
    def search_pop_points(self, value: str, max_zoom_iterations: int = 4) -> list[StorehouseData]:
        return self.search_storehouses(value, max_zoom_iterations=max_zoom_iterations)

    @step("Pobieram listę dostępnych punktów DHL POP")
    def get_available_pop_points(self, max_zoom_iterations: int = 4) -> list[StorehouseData]:
        return self.get_available_storehouses(max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram punkt DHL POP o nazwie: {point_name}")
    def choose_pop_point_by_name(self, point_name: str, max_zoom_iterations: int = 4) -> StorehouseData:
        return self.choose_storehouse_by_name(point_name, max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram punkt DHL POP o data-id: {point_data_id}")
    def choose_pop_point_by_data_id(self, point_data_id: str, max_zoom_iterations: int = 4) -> StorehouseData:
        return self.choose_storehouse_by_data_id(point_data_id, max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram losowy punkt DHL POP")
    def choose_random_pop_point(self, max_zoom_iterations: int = 4) -> StorehouseData:
        return self.choose_random_storehouse(max_zoom_iterations=max_zoom_iterations)


class DeliveryInpostReceiverOverlay(DeliveryStorehouseReceiverOverlay):
    OVERLAY_NAME = "Delivery InPost Receiver Overlay"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope)
        self.name = self.OVERLAY_NAME

    @step("Wyszukuję punkty InPost dla lokalizacji: {value}")
    def search_inpost_points(self, value: str, max_zoom_iterations: int = 4) -> list[StorehouseData]:
        return self.search_storehouses(value, max_zoom_iterations=max_zoom_iterations)

    @step("Pobieram listę dostępnych punktów InPost")
    def get_available_inpost_points(self, max_zoom_iterations: int = 4) -> list[StorehouseData]:
        return self.get_available_storehouses(max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram punkt InPost o nazwie: {point_name}")
    def choose_inpost_point_by_name(self, point_name: str, max_zoom_iterations: int = 4) -> StorehouseData:
        return self.choose_storehouse_by_name(point_name, max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram punkt InPost o data-id: {point_data_id}")
    def choose_inpost_point_by_data_id(self, point_data_id: str, max_zoom_iterations: int = 4) -> StorehouseData:
        return self.choose_storehouse_by_data_id(point_data_id, max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram losowy punkt InPost")
    def choose_random_inpost_point(self, max_zoom_iterations: int = 4) -> StorehouseData:
        return self.choose_random_storehouse(max_zoom_iterations=max_zoom_iterations)


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
