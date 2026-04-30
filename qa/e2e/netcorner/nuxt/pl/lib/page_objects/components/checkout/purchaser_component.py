from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class CheckoutPurchaserComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='purchaser']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Purchaser Component")

        self.__add_data_tile = self.find('[data-name="orderPickerTile"][data-role="dialogTrigger"]')
        self.__electronic_invoice_checkbox = self.find("#electronicInvoice")

    @step("Klikam kafelek kupującego: Dodaj dane")
    def click_add_data_tile(self) -> None:
        self.pointer_click(self.__add_data_tile)

    def is_electronic_invoice_checked(self) -> bool:
        return self.__electronic_invoice_checkbox.first.is_checked()

    @step("Ustawiam checkbox 'Faktura elektroniczna' na {enabled}")
    def set_electronic_invoice(self, enabled: bool = True) -> Self:
        checkbox = self.__electronic_invoice_checkbox.first
        if checkbox.is_checked() != enabled:
            self.pointer_click(checkbox)
        return self
