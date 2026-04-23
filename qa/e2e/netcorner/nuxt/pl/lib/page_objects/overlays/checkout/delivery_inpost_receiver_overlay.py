from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step

from .delivery_storehouse_receiver_overlay import DeliveryStorehouseReceiverOverlay
from .storehouse_data import StorehouseData


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
