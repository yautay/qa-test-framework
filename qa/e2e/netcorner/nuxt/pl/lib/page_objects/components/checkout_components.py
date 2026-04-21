from __future__ import annotations

import random
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Self

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    PaymentMethods,
    PaymentRequiredConsent,
)


def _get_visible_text(locator: Locator) -> str:
    element = locator.first
    if element.count() == 0 or not element.is_visible():
        return ""
    return (element.text_content() or "").strip()


@dataclass(frozen=True, slots=True)
class DeliveryTypeData:
    inpost: bool
    dhl_pop: bool
    courier_service: bool
    store_pickup: bool


class CheckoutDeliveryTypeComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='shippingMethod']"

    def __init__(self, scope: Page | Locator) -> None:
        if isinstance(scope, Page):
            root = scope.locator(self.ROOT_SELECTOR)
        else:
            product_in_scope = scope.locator(self.ROOT_SELECTOR)
            root = product_in_scope.first if product_in_scope.count() > 0 else scope

        super().__init__(root, name="Checkout Delivery Type Component")

        self.__storehouse_tile = self.find('[data-name="orderPickerTile"][data-provider="storehouse"]')
        self.__dhl_tile = self.find('[data-name="orderPickerTile"][data-provider="dhl"]')
        self.__inpost_tile = self.find('[data-name="orderPickerTile"][data-provider="inpost"]')
        self.__courier_tile = self.find('[data-name="orderPickerTile"][data-provider="courier"]')

    @step("Klikam kafelek dostawy: Salony")
    def click_storehouse_tile(self) -> None:
        self.safe_click(self.__storehouse_tile)

    @step("Klikam kafelek dostawy: DHL Automaty BOX i punkty POP")
    def click_dhl_tile(self) -> None:
        self.safe_click(self.__dhl_tile)

    @step("Klikam kafelek dostawy: InPost Paczkomat 24/7")
    def click_inpost_tile(self) -> None:
        self.safe_click(self.__inpost_tile)

    @step("Klikam kafelek dostawy: Wysyłka kurierem")
    def click_courier_tile(self) -> None:
        self.safe_click(self.__courier_tile)

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
        if isinstance(scope, Page):
            root = scope.locator(self.ROOT_SELECTOR)
        else:
            product_in_scope = scope.locator(self.ROOT_SELECTOR)
            root = product_in_scope.first if product_in_scope.count() > 0 else scope

        super().__init__(root, name="Checkout Delivery Object Component")

        self.__delivery_object_tile = self.find('[data-name="orderPickerTile"]')

    @step("Klikam kafelek odbiorcy dla wybranej metody transportu")
    def click_delivery_object_tile(self) -> None:
        self.safe_click(self.__delivery_object_tile)


class CheckoutPurchaserComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='purchaser']"

    def __init__(self, scope: Page | Locator) -> None:
        if isinstance(scope, Page):
            root = scope.locator(self.ROOT_SELECTOR)
        else:
            product_in_scope = scope.locator(self.ROOT_SELECTOR)
            root = product_in_scope.first if product_in_scope.count() > 0 else scope

        super().__init__(root, name="Checkout Purchaser Component")

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
        if isinstance(scope, Page):
            root = scope.locator(self.ROOT_SELECTOR)
        else:
            product_in_scope = scope.locator(self.ROOT_SELECTOR)
            root = product_in_scope.first if product_in_scope.count() > 0 else scope

        super().__init__(root, name="Checkout Delivery Methods Component")

        self.__list_container = self.find('[data-name="OrderDeliveryList"]')
        self.__matrix_container = self.find('[data-name="OrderDeliveryMatrix"]')
        self.__list_tiles = self.__list_container.locator('[data-name="orderPickerTile"]')
        self.__matrix_tiles = self.__matrix_container.locator(
            '[data-name="orderPickerTile"], [data-name="orderMatrixTile"], [data-name*="PickerTile"]'
        )
        self.__fallback_tiles = self.find('[data-name="orderPickerTile"]')

    def __visible_tiles(self, tiles: Locator) -> list[Locator]:
        return [tiles.nth(index) for index in range(tiles.count()) if tiles.nth(index).is_visible()]

    @staticmethod
    def __normalize_tile_text(tile: Locator) -> str:
        return " ".join(_get_visible_text(tile).split())

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
        if self.__list_container.first.is_visible():
            return DeliveryMethodsLayout.LIST, self.__get_available_methods_list()
        if self.__matrix_container.first.is_visible():
            return DeliveryMethodsLayout.MATRIX, self.__get_available_methods_matrix()
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

        self.safe_click(random.choice(available_tiles))
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
        if isinstance(scope, Page):
            root = scope.locator(self.ROOT_SELECTOR)
        else:
            product_in_scope = scope.locator(self.ROOT_SELECTOR)
            root = product_in_scope.first if product_in_scope.count() > 0 else scope

        super().__init__(root, name="Checkout Payment Methods Component")

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
        return " ".join(_get_visible_text(tile).split())

    @staticmethod
    def __normalize_label(text: str) -> str:
        return " ".join(text.split()).casefold()

    def __method_name_from_tile(self, tile: Locator) -> str:
        title = _get_visible_text(tile.locator("p").first)
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
