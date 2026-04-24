from __future__ import annotations

import random
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text
from qa.e2e.netcorner.nuxt.pl.lib.test_data.checkout.checkout_data_models import (
    PaymentMethods,
    PaymentRequiredConsent,
)


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
        self.__comment_checkbox = self.find("#orderUserCommentCheckbox")

    def __visible_tiles(self) -> list[Locator]:
        visible_tiles: list[Locator] = []
        for index in range(self.__payment_tiles.count()):
            tile = self.__payment_tiles.nth(index)
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
        field = self.find("textarea").first
        expect(field).to_be_visible(timeout=2_000)
        return field

    def __set_checkbox(self, checkbox: Locator, enabled: bool) -> None:
        target = checkbox.first
        if target.is_checked() != enabled:
            self.pointer_click(target)

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
                self.pointer_click(tile)
                return surcharge

        raise RuntimeError(f"Nie znaleziono dostępnej metody płatności: {payment_method.name}")

    @step("Wybieram losową dostępną metodę płatności")
    def choose_random_available_method(self) -> Decimal:
        available_tiles = self.__visible_tiles()
        if not available_tiles:
            raise RuntimeError("Brak dostępnych metod płatności do wyboru.")

        tile = random.choice(available_tiles)
        surcharge = self.__parse_surcharge(self.__normalize_tile_text(tile))
        self.pointer_click(tile)
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
