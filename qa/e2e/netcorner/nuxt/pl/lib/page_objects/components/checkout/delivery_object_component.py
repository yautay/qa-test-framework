from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class CheckoutDeliveryObjectComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='orderParcelPicker'], [data-name='OrderReceiverPicker']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(scope.locator(self.ROOT_SELECTOR), name="Checkout Delivery Object Component")

        self.__delivery_object_tile = self.root.locator('[data-name="orderPickerTile"][data-role="dialogTrigger"]')

    @step("Klikam kafelek odbiorcy dla wybranej metody transportu")
    def click_delivery_object_tile(self) -> None:
        self.pointer_click(self.__delivery_object_tile)
