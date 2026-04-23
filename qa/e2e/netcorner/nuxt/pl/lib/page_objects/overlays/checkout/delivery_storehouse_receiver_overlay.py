from __future__ import annotations

import random
from collections.abc import Callable
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent

from .storehouse_data import StorehouseData


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
