from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Self

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


@dataclass(frozen=True, slots=True)
class DeliveryTypeData:
    inpost: bool
    dhl_pop: bool
    courier_service: bool
    store_pickup: bool


class CheckoutDeliveryTypeComponent(BaseComponent):
    ROOT_SELECTOR = "[data-picker='shippingMethod']"
    PROVIDER_SELECTION_TIMEOUT_MS = 5_000
    PROVIDER_SELECTION_POLL_MS = 100

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Checkout Delivery Type Component")

        self.__storehouse_tile = self.find('[data-name="orderPickerTile"][data-provider="storehouse"]')
        self.__dhl_tile = self.find('[data-name="orderPickerTile"][data-provider="dhl"]')
        self.__inpost_tile = self.find('[data-name="orderPickerTile"][data-provider="inpost"]')
        self.__courier_tile = self.find('[data-name="orderPickerTile"][data-provider="courier"]')

    @step("Klikam kafelek dostawy: Salony")
    def click_storehouse_tile(self) -> Self:
        self.pointer_click(self.__storehouse_tile)
        return self

    @step("Klikam kafelek dostawy: DHL Automaty BOX i punkty POP")
    def click_dhl_tile(self) -> Self:
        self.pointer_click(self.__dhl_tile)
        return self

    @step("Klikam kafelek dostawy: InPost Paczkomat 24/7")
    def click_inpost_tile(self) -> Self:
        self.pointer_click(self.__inpost_tile)
        return self

    @step("Klikam kafelek dostawy: Wysyłka kurierem")
    def click_courier_tile(self) -> Self:
        self.pointer_click(self.__courier_tile)
        return self

    def get_delivery_type_availability(self) -> DeliveryTypeData:
        return DeliveryTypeData(
            inpost=self.__inpost_tile.is_visible(),
            dhl_pop=self.__dhl_tile.is_visible(),
            courier_service=self.__courier_tile.is_visible(),
            store_pickup=self.__storehouse_tile.is_visible(),
        )

    def __delivery_tiles(self) -> list[Locator]:
        return [self.__storehouse_tile, self.__dhl_tile, self.__inpost_tile, self.__courier_tile]

    @staticmethod
    def __tile_provider(tile: Locator) -> str:
        return (tile.get_attribute("data-provider") or "").strip().lower()

    @staticmethod
    def __is_tile_selected(tile: Locator) -> bool:
        # Primary signal: stable CSS border class on the tile article element.
        # The tile receives `border-blue-clear` when selected and `border-gray-mercury`
        # when not selected. This class is set by the server/hydration and does not
        # flicker during AJAX re-renders of transport cost, unlike the `i-verify` icon
        # inside `tileSelectIndicator` which is toggled via a Vue transition and can
        # momentarily disappear while the checkout recalculates shipping.
        classes = tile.get_attribute("class") or ""
        return "border-blue-clear" in classes

    def __selected_provider_once(self) -> str:
        for tile_locator in self.__delivery_tiles():
            tile = tile_locator.first
            if tile.count() == 0 or not tile.is_visible():
                continue
            provider = self.__tile_provider(tile)
            if provider and self.__is_tile_selected(tile):
                return provider
        return ""

    def get_selected_delivery_provider(self, timeout: int | None = None) -> str:
        deadline = time.monotonic() + ((timeout or self.PROVIDER_SELECTION_TIMEOUT_MS) / 1000)
        stable_provider = ""
        stable_passes = 0

        while time.monotonic() < deadline:
            current_provider = self.__selected_provider_once()
            if current_provider and current_provider == stable_provider:
                stable_passes += 1
                if stable_passes >= 1:
                    return current_provider
            elif current_provider:
                stable_provider = current_provider
                stable_passes = 0
            else:
                stable_provider = ""
                stable_passes = 0
            self.root.page.wait_for_timeout(self.PROVIDER_SELECTION_POLL_MS)

        raise RuntimeError("Nie udało się rozpoznać aktywnego typu dostawy.")
