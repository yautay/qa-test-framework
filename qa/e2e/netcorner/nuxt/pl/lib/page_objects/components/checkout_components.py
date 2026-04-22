from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Self

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    PaymentMethods,
    PaymentRequiredConsent,
)


@dataclass(frozen=True, slots=True)
class DeliveryTypeData:
    inpost: bool
    dhl_pop: bool
    courier_service: bool
    store_pickup: bool


class CheckoutDeliveryTypeComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='shippingMethod']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Delivery Type Component")

        self.__storehouse_tile = self.find('[data-name="orderPickerTile"][data-provider="storehouse"]')
        self.__dhl_tile = self.find('[data-name="orderPickerTile"][data-provider="dhl"]')
        self.__inpost_tile = self.find('[data-name="orderPickerTile"][data-provider="inpost"]')
        self.__courier_tile = self.find('[data-name="orderPickerTile"][data-provider="courier"]')

    @step("Klikam kafelek dostawy: Salony")
    def click_storehouse_tile(self) -> Self:
        self.safe_click(self.__storehouse_tile)
        return self

    @step("Klikam kafelek dostawy: DHL Automaty BOX i punkty POP")
    def click_dhl_tile(self) -> Self:
        self.safe_click(self.__dhl_tile)
        return self

    @step("Klikam kafelek dostawy: InPost Paczkomat 24/7")
    def click_inpost_tile(self) -> Self:
        self.safe_click(self.__inpost_tile)
        return self

    @step("Klikam kafelek dostawy: Wysyłka kurierem")
    def click_courier_tile(self) -> Self:
        self.safe_click(self.__courier_tile)
        return self

    def get_delivery_type_availability(self) -> DeliveryTypeData:
        return DeliveryTypeData(
            inpost=self.__inpost_tile.is_visible(),
            dhl_pop=self.__dhl_tile.is_visible(),
            courier_service=self.__courier_tile.is_visible(),
            store_pickup=self.__storehouse_tile.is_visible(),
        )


class CheckoutDeliveryObjectComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='receiver']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Delivery Object Component")

        self.__delivery_object_tile = self.find('[data-name="orderPickerTile"]')

    @step("Klikam kafelek odbiorcy dla wybranej metody transportu")
    def click_delivery_object_tile(self) -> None:
        self.safe_click(self.__delivery_object_tile)


class CheckoutPurchaserComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='purchaser']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Purchaser Component")

        self.__add_data_tile = self.find('[data-name="orderPickerTile"]:has-text("Dodaj dane")')
        self.__fallback_tile = self.find('[data-name="orderPickerTile"]')
        self.__electronic_invoice_checkbox = self.find("#electronicInvoice")

    @step("Klikam kafelek kupującego: Dodaj dane")
    def click_add_data_tile(self) -> None:
        if self.__add_data_tile.count() > 0:
            self.safe_click(self.__add_data_tile)
            return
        self.safe_click(self.__fallback_tile)

    def is_electronic_invoice_checked(self) -> bool:
        checkbox = self.__electronic_invoice_checkbox.first
        if checkbox.count() == 0 or not checkbox.is_visible():
            return False
        return checkbox.is_checked()

    @step("Ustawiam checkbox 'Faktura elektroniczna' na {enabled}")
    def set_electronic_invoice(self, enabled: bool = True) -> Self:
        checkbox = self.__electronic_invoice_checkbox.first
        if checkbox.count() == 0 or not checkbox.is_visible():
            return self

        if checkbox.is_checked() != enabled:
            self.safe_click(checkbox)
        return self


class DeliveryMethodsLayout(StrEnum):
    LIST = "lista metod transportu"
    MATRIX = "macierz metod transportu"


class CheckoutDeliveryMethodsComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='delivery']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Delivery Methods Component")

        self.__list_container = self.find('[data-name="OrderDeliveryList"]')
        self.__matrix_container = self.find('[data-name="OrderDeliveryMatrix"]')
        self.__list_tiles = self.__list_container.locator('[data-name="orderPickerTile"]')
        self.__matrix_tiles = self.__matrix_container.locator(
            '[data-name="orderPickerTile"], [data-name="orderMatrixTile"], [data-name*="PickerTile"]'
        )
        self.__fallback_tiles = self.find('[data-name="orderPickerTile"]')

    @step("Czekam na dostępne metody transportu")
    def wait_for_available_methods(self, timeout: int | None = None) -> Self:
        deadline = time.monotonic() + ((timeout or self.DEFAULT_TIMEOUT) / 1000)
        while time.monotonic() < deadline:
            if self.__list_container.first.is_visible() and self.__visible_tiles(self.__list_tiles):
                return self
            if self.__matrix_container.first.is_visible() and self.__visible_tiles(self.__matrix_tiles):
                return self
            if self.__visible_tiles(self.__fallback_tiles):
                return self
            self.root.page.wait_for_timeout(250)

        raise RuntimeError("Brak dostępnych metod transportu po uzupełnieniu danych odbiorcy.")

    @staticmethod
    def __is_tile_selectable(tile: Locator) -> bool:
        if not tile.is_visible():
            return False

        disabled = (tile.get_attribute("disabled") or "").strip().lower()
        if disabled in {"true", "disabled"}:
            return False

        aria_disabled = (tile.get_attribute("aria-disabled") or "").strip().lower()
        if aria_disabled == "true":
            return False

        classes = (tile.get_attribute("class") or "").strip().lower()
        if "pointer-events-none" in classes:
            return False

        return True

    def __visible_tiles(self, tiles: Locator) -> list[Locator]:
        visible_tiles: list[Locator] = []
        for index in range(tiles.count()):
            tile = tiles.nth(index)
            if self.__is_tile_selectable(tile):
                visible_tiles.append(tile)
        return visible_tiles

    @staticmethod
    def __normalize_tile_text(tile: Locator) -> str:
        return " ".join(get_visible_text(tile).split())

    def __tile_sort_key(self, tile: Locator) -> tuple[float, float]:
        box = tile.bounding_box() or {"x": 0.0, "y": 0.0}
        return float(box["y"]), float(box["x"])

    def __get_available_methods_list(self) -> list[str]:
        methods = [self.__normalize_tile_text(tile) for tile in self.__visible_tiles(self.__list_tiles)]
        return [method for method in methods if method]

    def __get_available_methods_matrix(self) -> list[list[str]]:
        tiles = self.__visible_tiles(self.__matrix_tiles)

        if not tiles:
            tiles = self.__visible_tiles(self.__matrix_container.locator('[data-name="orderPickerTile"]'))

        if not tiles:
            return []

        sorted_tiles = sorted(tiles, key=self.__tile_sort_key)
        row_tolerance = 20.0
        rows: list[list[Locator]] = []

        for tile in sorted_tiles:
            tile_y, _ = self.__tile_sort_key(tile)
            if not rows:
                rows.append([tile])
                continue

            first_row_tile_y, _ = self.__tile_sort_key(rows[-1][0])
            if abs(tile_y - first_row_tile_y) <= row_tolerance:
                rows[-1].append(tile)
            else:
                rows.append([tile])

        matrix: list[list[str]] = []
        for row in rows:
            row_sorted = sorted(row, key=lambda tile: self.__tile_sort_key(tile)[1])
            row_methods = [self.__normalize_tile_text(tile) for tile in row_sorted]
            cleaned_row = [method for method in row_methods if method]
            if cleaned_row:
                matrix.append(cleaned_row)

        return matrix

    def get_methods_layout(self) -> tuple[DeliveryMethodsLayout, list[str] | list[list[str]]]:
        self.wait_for_available_methods()
        if self.__list_container.first.is_visible():
            return DeliveryMethodsLayout.LIST, self.__get_available_methods_list()
        if self.__matrix_container.first.is_visible():
            return DeliveryMethodsLayout.MATRIX, self.__get_available_methods_matrix()
        fallback_methods = [self.__normalize_tile_text(tile) for tile in self.__visible_tiles(self.__fallback_tiles)]
        if fallback_methods:
            return DeliveryMethodsLayout.LIST, [method for method in fallback_methods if method]
        raise RuntimeError("Nie udało się rozpoznać układu metod transportu.")

    @step("Wybieram losową dostępną metodę transportu i przechodzę dalej")
    def choose_random_available_method(self) -> DeliveryMethodsLayout:
        layout, _ = self.get_methods_layout()

        if layout == DeliveryMethodsLayout.LIST:
            available_tiles = self.__visible_tiles(self.__list_tiles)
        else:
            available_tiles = self.__visible_tiles(self.__matrix_tiles)

        if not available_tiles:
            available_tiles = self.__visible_tiles(self.__fallback_tiles)

        if not available_tiles:
            raise RuntimeError("Brak dostępnych metod transportu do wyboru.")

        candidates = available_tiles[:]
        random.shuffle(candidates)
        for tile in candidates:
            try:
                tile.click(timeout=3_000, trial=True)
                self.safe_click(tile)
                return layout
            except PlaywrightTimeoutError:
                continue

        raise RuntimeError("Nie udało się kliknąć żadnej dostępnej metody transportu.")
        return layout


@dataclass(frozen=True, slots=True)
class PaymentMethodData:
    name: str
    surcharge: Decimal


class CheckoutPaymentMethodsComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='paymentMethod']"
    _SENTINEL_SURCHARGE = Decimal("0.00")
    _SURCHARGE_PATTERN = re.compile(r"([+-]?)\s*(\d+(?:[\.,]\d{1,2})?)\s*(?:zł|zl|PLN)", re.IGNORECASE)
    _METHOD_LABELS: dict[PaymentMethods, tuple[str, ...]] = {
        PaymentMethods.BLIK: ("BLIK",),
        PaymentMethods.PREPAID_TRANSFER: ("Przelew - przedpłata",),
        PaymentMethods.CASH_ON_DELIVERY_CASH: ("Za pobraniem - płatność gotówką",),
        PaymentMethods.CASH_ON_DELIVERY_CARD: ("Za pobraniem - płatność kartą",),
    }
    _REQUIRED_CONSENT_SELECTORS: dict[PaymentRequiredConsent, str] = {
        PaymentRequiredConsent.REGULATION: "#regulation",
    }

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Payment Methods Component")

        self.__payment_picker = self.find('[data-name="orderPaymentPicker"]')
        self.__payment_tiles = self.__payment_picker.locator('[data-name="orderPickerTile"]')
        self.__fallback_tiles = self.find('[data-name="orderPickerTile"]')
        self.__comment_checkbox = self.find("#orderUserCommentCheckbox")

    def __visible_tiles(self) -> list[Locator]:
        source_tiles = self.__payment_tiles
        if source_tiles.count() == 0:
            source_tiles = self.__fallback_tiles

        visible_tiles: list[Locator] = []
        for index in range(source_tiles.count()):
            tile = source_tiles.nth(index)
            if tile.is_visible():
                visible_tiles.append(tile)
        return visible_tiles

    @staticmethod
    def __normalize_tile_text(tile: Locator) -> str:
        return " ".join(get_visible_text(tile).split())

    @staticmethod
    def __normalize_label(text: str) -> str:
        return " ".join(text.split()).casefold()

    def __method_name_from_tile(self, tile: Locator) -> str:
        title = get_visible_text(tile.locator("p").first)
        if title:
            return " ".join(title.split())
        return self.__normalize_tile_text(tile)

    @classmethod
    def __parse_surcharge(cls, text: str) -> Decimal:
        match = cls._SURCHARGE_PATTERN.search(text)
        if not match:
            return cls._SENTINEL_SURCHARGE

        sign = match.group(1)
        numeric = match.group(2).replace(",", ".")
        try:
            amount = Decimal(numeric).quantize(Decimal("0.01"))
        except InvalidOperation:
            return cls._SENTINEL_SURCHARGE

        if sign == "-":
            return -amount
        return amount

    @classmethod
    def __matches_payment_method(cls, tile_name: str, payment_method: PaymentMethods) -> bool:
        normalized_tile_name = cls.__normalize_label(tile_name)
        return any(cls.__normalize_label(label) in normalized_tile_name for label in cls._METHOD_LABELS[payment_method])

    def __resolve_comment_field(self) -> Locator:
        selectors = [
            "textarea",
            "[data-name*='comment'] textarea",
            "[name*='comment']:not([type='checkbox'])",
            "[id*='comment']:not([type='checkbox'])",
        ]

        for selector in selectors:
            candidate = self.find(selector).first
            try:
                candidate.wait_for(state="visible", timeout=2_000)
                return candidate
            except Exception:
                continue

        raise RuntimeError("Nie znaleziono pola komentarza do zamówienia po zaznaczeniu checkboxa.")

    def __set_checkbox(self, checkbox: Locator, enabled: bool) -> None:
        target = checkbox.first
        if target.count() == 0 or not target.is_visible():
            return
        if target.is_checked() != enabled:
            self.safe_click(target)

    def get_available_payment_methods(self) -> list[PaymentMethodData]:
        methods: list[PaymentMethodData] = []
        for tile in self.__visible_tiles():
            tile_text = self.__normalize_tile_text(tile)
            methods.append(
                PaymentMethodData(
                    name=self.__method_name_from_tile(tile),
                    surcharge=self.__parse_surcharge(tile_text),
                )
            )
        return methods

    @step("Wybieram metodę płatności: {payment_method}")
    def choose_payment_method(self, payment_method: PaymentMethods) -> Decimal:
        for tile in self.__visible_tiles():
            tile_name = self.__method_name_from_tile(tile)
            if self.__matches_payment_method(tile_name, payment_method):
                surcharge = self.__parse_surcharge(self.__normalize_tile_text(tile))
                self.safe_click(tile)
                return surcharge

        raise RuntimeError(f"Nie znaleziono dostępnej metody płatności: {payment_method.name}")

    @step("Wybieram losową dostępną metodę płatności")
    def choose_random_available_method(self) -> Decimal:
        available_tiles = self.__visible_tiles()
        if not available_tiles:
            raise RuntimeError("Brak dostępnych metod płatności do wyboru.")

        tile = random.choice(available_tiles)
        surcharge = self.__parse_surcharge(self.__normalize_tile_text(tile))
        self.safe_click(tile)
        return surcharge

    @step("Ustawiam checkbox komentarza do zamówienia na {enabled}")
    def set_order_comment_enabled(self, enabled: bool = True) -> Self:
        self.__set_checkbox(self.__comment_checkbox, enabled)
        return self

    @step("Wpisuję komentarz do zamówienia")
    def set_order_comment(self, comment: str) -> Self:
        normalized_comment = comment.strip()
        if not normalized_comment:
            return self

        self.set_order_comment_enabled(True)
        self.safe_fill(self.__resolve_comment_field(), normalized_comment)
        return self

    @step("Ustawiam wymaganą zgodę {consent} na {enabled}")
    def set_required_consent(self, consent: PaymentRequiredConsent, enabled: bool = True) -> Self:
        selector = self._REQUIRED_CONSENT_SELECTORS[consent]
        self.__set_checkbox(self.find(selector), enabled)
        return self

    @step("Ustawiam wymagane zgody zamówienia")
    def set_required_consents(self, consents: tuple[PaymentRequiredConsent, ...], enabled: bool = True) -> Self:
        for consent in consents:
            self.set_required_consent(consent, enabled)
        return self


@dataclass(frozen=True, slots=True)
class CheckoutSummaryData:
    delivery_price: str
    delivery_surcharge: Decimal
    total_to_pay: str


class CheckoutSummaryComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='paymentMethod']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Summary Component")

        self.__summary_panel = self.root.page.locator("section,div,aside").filter(
            has=self.root.page.get_by_role("heading", name="Podsumowanie koszyka")
        ).first
        self.__delivery_price = self.find("css=div:has(> span:text-is('Dostawa')) >> span.font-semibold")
        self.__payment_fee = self.find("css=p:text-is('Płatność') + div >> span.block.text-right")
        self.__total_to_pay = self.find("css=p.font-semibold:text-is('Do zapłaty') + span >> span.block.text-right")
        self.__place_order_button = self.root.page.get_by_role("button", name="Zamawiam z obowiązkiem zapłaty").first

    @staticmethod
    def __read_text(locator: Locator, timeout: int = 1_000) -> str:
        try:
            return (locator.first.text_content(timeout=timeout) or "").strip()
        except Exception:
            return ""

    @staticmethod
    def __parse_money(value: str) -> Decimal:
        match = re.search(r"([+-]?\d+(?:[\.,]\d{1,2})?)", value)
        if not match:
            return Decimal("0.00")
        try:
            return Decimal(match.group(1).replace(",", ".")).quantize(Decimal("0.01"))
        except InvalidOperation:
            return Decimal("0.00")

    @step("Klikam przycisk złożenia zamówienia")
    def click_place_order(self) -> CheckoutSummaryData:
        summary_data = CheckoutSummaryData(
            delivery_price=self.__get_delivery_price(),
            delivery_surcharge=self.__parse_money(self.__get_payment_fee()),
            total_to_pay=self.__get_total_to_pay(),
        )
        self.safe_click(self.__place_order_button)
        return summary_data

    def __get_delivery_price(self) -> str:
        return self.__read_text(self.__delivery_price) or self.__read_text(self.__summary_panel)

    def __get_payment_fee(self) -> str:
        return self.__read_text(self.__payment_fee) or self.__read_text(self.__summary_panel)

    def __get_total_to_pay(self) -> str:
        return self.__read_text(self.__total_to_pay) or self.__read_text(self.__summary_panel)


@dataclass(frozen=True, slots=True)
class TypSummaryData:
    order_number: str
    planned_delivery: str
    delivery_address: str
    delivery_cost: str
    sms_status_cost: str
    payment_cost: str
    total_to_pay: str


class TypSummaryComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="TypSummaryComponent")

        # locators (private)
        self.__order_number = self.find("p.text-lg.font-medium")
        self.__planned_delivery = self.find("p:has-text('Planowana dostawa twojego zamówienia:') + div span")
        self.__delivery_address = self.find("p:has-text('Adres dostawy:') + div span")
        self.__delivery_cost = self.find("span:text-is('Dostawa') + span.font-semibold")
        self.__sms_status_cost = self.find("span:text-is('SMS Status zamówienia') + span.font-semibold")
        self.__payment_cost = self.find("p:text-is('Płatność') + div span.block.text-right")
        self.__total_to_pay = self.find("p:text-is('Do zapłaty') + span span.block.text-right")

    # getters
    def __get_order_number(self) -> str:
        return (self.__order_number.text_content() or "").strip()

    def __get_planned_delivery(self) -> str:
        return (self.__planned_delivery.text_content() or "").strip()

    def __get_delivery_address(self) -> str:
        return (self.__delivery_address.text_content() or "").strip()

    def __get_delivery_cost(self) -> str:
        return (self.__delivery_cost.text_content() or "").strip()

    def __get_sms_status_cost(self) -> str:
        return (self.__sms_status_cost.text_content() or "").strip()

    def __get_payment_cost(self) -> str:
        return (self.__payment_cost.text_content() or "").strip()

    def __get_total_to_pay(self) -> str:
        return (self.__total_to_pay.text_content() or "").strip()

    def get_summary_data(self) -> TypSummaryData:
        return TypSummaryData(
            order_number=self.__get_order_number(),
            planned_delivery=self.__get_planned_delivery(),
            delivery_address=self.__get_delivery_address(),
            delivery_cost=self.__get_delivery_cost(),
            sms_status_cost=self.__get_sms_status_cost(),
            payment_cost=self.__get_payment_cost(),
            total_to_pay=self.__get_total_to_pay(),
        )
