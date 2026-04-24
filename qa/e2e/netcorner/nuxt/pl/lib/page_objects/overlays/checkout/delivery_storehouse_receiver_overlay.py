from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent

from .common import _order_pickup_dialog_root
from .storehouse_data import StorehouseData


class DeliveryStorehouseReceiverOverlay(BaseComponent):
    DIALOG_HEADING_PATTERN = r"Dodaj punkt odbioru|Delivery (DHL POP|InPost|Storehouse) Receiver Overlay"
    MAP_SELECTOR = 'div[data-name="orderMap"]'
    MAP_SETTLE_TIMEOUT_MS = 2_000
    MAP_STABILITY_POLL_MS = 250
    MAP_STABILITY_REQUIRED_PASSES = 1
    MAX_ALERT_GUIDED_ZOOM_STEPS = 40

    def __init__(self, scope: Page | Locator) -> None:
        root = _order_pickup_dialog_root(scope, self.DIALOG_HEADING_PATTERN)
        super().__init__(root, name="Delivery Storehouse Receiver Overlay")

        self.__map_root = self.find(self.MAP_SELECTOR)
        self.__visit_us_input = self.__map_root.locator("#visitUs")
        self.__search_button = self.__map_root.locator('[data-name="searchInput"] button:has(i.i-search)')
        self.__parcel_list = self.__map_root.locator('[data-name="parcelList"]')
        self.__storehouse_tiles = self.__parcel_list.locator('[data-name="orderPickerTile"]')
        self.__map_list_alert = self.__map_root.locator('[data-name="mapListAlert"]')
        self.__close_button = self.find('button:has-text("Zamknij okno"):visible')
        self.__zoom_in_button = self.__map_root.locator('[aria-label="Zoom in"]')
        self.__zoom_out_button = self.__map_root.locator('[aria-label="Zoom out"]')

    @staticmethod
    def __normalize_text(value: str) -> str:
        return " ".join(value.split())

    def __get_map_alert_text(self) -> str:
        alert = self.__map_list_alert.first
        if alert.count() == 0 or not alert.is_visible():
            return ""
        return self.__normalize_text((alert.text_content() or "").strip())

    def __wait_for_map_view_stable(self, timeout: int | None = None) -> None:
        deadline = time.monotonic() + ((timeout or self.DEFAULT_TIMEOUT) / 1000)
        stable_passes = 0
        last_snapshot: tuple[int, str] | None = None

        while time.monotonic() < deadline:
            visible_tiles_count = len(self.__visible_storehouse_tiles())
            map_alert_text = self.__get_map_alert_text()
            snapshot = (visible_tiles_count, map_alert_text)

            if snapshot == last_snapshot and (visible_tiles_count > 0 or map_alert_text):
                stable_passes += 1
                if stable_passes >= self.MAP_STABILITY_REQUIRED_PASSES:
                    return
            else:
                stable_passes = 0
                last_snapshot = snapshot

            self.root.page.wait_for_timeout(self.MAP_STABILITY_POLL_MS)

        raise RuntimeError("Nie udało się ustabilizować widoku mapy punktów odbioru.")

    def __wait_for_storehouses(self, timeout: int | None = None) -> None:
        expect(self.root).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        expect(self.__map_root).to_be_visible(timeout=timeout or self.DEFAULT_TIMEOUT)
        self.root.page.wait_for_timeout(self.MAP_SETTLE_TIMEOUT_MS)
        self.__wait_for_map_view_stable(timeout=timeout)

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

        name_locator = tile.locator("p[title]").first
        if name_locator.count() == 0:
            return None

        name = self.__normalize_text((name_locator.text_content() or "").strip())
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
        self.pointer_click(button)
        self.__wait_for_storehouses(timeout=8_000)
        return True

    def __close_picker_modal_after_selection(self) -> None:
        if not self.root.is_visible():
            return

        target = self.__close_button.first
        if target.count() == 0 or not target.is_visible():
            raise RuntimeError("Nie znaleziono przycisku zamknięcia okna wyboru punktu odbioru.")

        self.pointer_click(self.__close_button)
        self.wait_hidden(timeout=10_000)

    def __select_storehouse_tile(self, tile: Locator) -> None:
        self.pointer_click(tile)
        self.__close_picker_modal_after_selection()

    def __zoom_out(self) -> bool:
        return self.__click_zoom_button(self.__zoom_out_button)

    def __zoom_in(self) -> bool:
        return self.__click_zoom_button(self.__zoom_in_button)

    def __collect_visible_storehouses(self) -> list[StorehouseData]:
        return [storehouse_data for _, storehouse_data in self.__collect_visible_storehouse_options()]

    def __collect_visible_storehouse_options(self) -> list[tuple[Locator, StorehouseData]]:
        unique_by_id: dict[str, StorehouseData] = {}
        tiles_by_id: dict[str, Locator] = {}
        for tile in self.__visible_storehouse_tiles():
            storehouse_data = self.__read_storehouse_data(tile)
            if storehouse_data is None:
                continue
            unique_by_id[storehouse_data.data_id] = storehouse_data
            tiles_by_id[storehouse_data.data_id] = tile
        return [(tiles_by_id[data_id], storehouse_data) for data_id, storehouse_data in unique_by_id.items()]

    def __guided_zoom_steps(self, max_zoom_iterations: int) -> int:
        if max_zoom_iterations <= 0:
            return self.MAX_ALERT_GUIDED_ZOOM_STEPS
        return min(max_zoom_iterations, self.MAX_ALERT_GUIDED_ZOOM_STEPS)

    def __map_alert_zoom_direction(self) -> str | None:
        alert_text = self.__get_map_alert_text().casefold()
        if not alert_text:
            return None

        if "powiększ mapę" in alert_text or "powieksz mape" in alert_text:
            return "in"

        if "oddal mapę" in alert_text or "oddal mape" in alert_text:
            return "out"

        return None

    def __zoom_by_direction(self, direction: str) -> bool:
        if direction == "in":
            return self.__zoom_in()
        if direction == "out":
            return self.__zoom_out()
        return False

    def __find_matching_storehouse(
        self,
        matcher: Callable[[StorehouseData], bool],
    ) -> tuple[Locator, StorehouseData] | None:
        for tile, storehouse_data in self.__collect_visible_storehouse_options():
            if matcher(storehouse_data):
                return tile, storehouse_data
        return None

    def __try_choose_matching_storehouse(self, matcher: Callable[[StorehouseData], bool]) -> StorehouseData | None:
        matched_storehouse = self.__find_matching_storehouse(matcher)
        if matched_storehouse is None:
            return None

        tile, storehouse_data = matched_storehouse
        self.__select_storehouse_tile(tile)
        return storehouse_data

    def __choose_with_alert_guidance(
        self,
        matcher: Callable[[StorehouseData], bool],
        max_zoom_iterations: int,
    ) -> StorehouseData | None:
        for _ in range(self.__guided_zoom_steps(max_zoom_iterations)):
            direction = self.__map_alert_zoom_direction()
            if direction is None:
                return None

            if not self.__zoom_by_direction(direction):
                return None

            selected_storehouse = self.__try_choose_matching_storehouse(matcher)
            if selected_storehouse is not None:
                return selected_storehouse

        return None

    def __collect_with_alert_guidance(self, max_zoom_iterations: int) -> list[StorehouseData]:
        for _ in range(self.__guided_zoom_steps(max_zoom_iterations)):
            direction = self.__map_alert_zoom_direction()
            if direction is None:
                return []

            if not self.__zoom_by_direction(direction):
                return []

            available_storehouses = self.__collect_visible_storehouses()
            if available_storehouses:
                return available_storehouses

        return []

    def __collect_storehouses_with_zoom(self, max_zoom_iterations: int = 40) -> list[StorehouseData]:
        self.__wait_for_storehouses()

        available_storehouses = self.__collect_visible_storehouses()
        if available_storehouses:
            return available_storehouses

        available_storehouses = self.__collect_with_alert_guidance(max_zoom_iterations=max_zoom_iterations)
        if available_storehouses:
            return available_storehouses

        return []

    def __choose_storehouse(
        self,
        matcher: Callable[[StorehouseData], bool],
        max_zoom_iterations: int = 40,
    ) -> StorehouseData:
        self.__wait_for_storehouses()

        selected_storehouse = self.__try_choose_matching_storehouse(matcher)
        if selected_storehouse is not None:
            return selected_storehouse

        selected_storehouse = self.__choose_with_alert_guidance(matcher, max_zoom_iterations=max_zoom_iterations)
        if selected_storehouse is not None:
            return selected_storehouse

        raise RuntimeError("Nie znaleziono salonu spełniającego kryteria wyboru.")

    @step("Uzupełniam kod pocztowy lub miasto: {value}")
    def fill_visit_us(self, value: str) -> Self:
        self.safe_fill(self.__visit_us_input, value)
        return self

    @step("Klikam ikonę wyszukiwania")
    def click_search_icon(self) -> Self:
        self.pointer_click(self.__search_button)
        return self

    @step("Wyszukuję salony dla lokalizacji: {value}")
    def search_storehouses(self, value: str, max_zoom_iterations: int = 40) -> list[StorehouseData]:
        self.fill_visit_us(value)
        self.click_search_icon()
        return self.get_available_storehouses(max_zoom_iterations=max_zoom_iterations)

    @step("Pobieram listę dostępnych salonów")
    def get_available_storehouses(self, max_zoom_iterations: int = 40) -> list[StorehouseData]:
        return self.__collect_storehouses_with_zoom(max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram salon o nazwie: {storehouse_name}")
    def choose_storehouse_by_name(self, storehouse_name: str, max_zoom_iterations: int = 40) -> StorehouseData:
        normalized_target = self.__normalize_text(storehouse_name).casefold()
        if not normalized_target:
            raise ValueError("Nazwa salonu nie może być pusta.")

        def matcher(storehouse: StorehouseData) -> bool:
            normalized_name = self.__normalize_text(storehouse.name).casefold()
            return normalized_target in normalized_name

        return self.__choose_storehouse(matcher, max_zoom_iterations=max_zoom_iterations)

    @step("Wybieram salon o data-id: {storehouse_data_id}")
    def choose_storehouse_by_data_id(self, storehouse_data_id: str, max_zoom_iterations: int = 40) -> StorehouseData:
        normalized_target = storehouse_data_id.strip()
        if not normalized_target:
            raise ValueError("data-id salonu nie może być puste.")

        return self.__choose_storehouse(
            lambda storehouse: storehouse.data_id == normalized_target,
            max_zoom_iterations=max_zoom_iterations,
        )

    @step("Wybieram losowy salon")
    def choose_random_storehouse(self, max_zoom_iterations: int = 40) -> StorehouseData:
        self.__wait_for_storehouses()

        available_options = self.__collect_visible_storehouse_options()
        if not available_options:
            self.__collect_with_alert_guidance(max_zoom_iterations=max_zoom_iterations)
            available_options = self.__collect_visible_storehouse_options()

        if not available_options:
            raise RuntimeError("Brak dostępnych salonów do wyboru.")

        tile, selected_storehouse = random.choice(available_options)
        self.__select_storehouse_tile(tile)
        return selected_storehouse
