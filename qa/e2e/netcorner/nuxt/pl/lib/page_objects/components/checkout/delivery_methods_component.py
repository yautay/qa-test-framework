from __future__ import annotations

import random
import time
from enum import StrEnum

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent
from qa.e2e.netcorner.nuxt.pl.lib.timeouts import QUICK_PROBE_MS
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.utils import get_visible_text


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

    @step("Czekam na dostępne metody transportu")
    def wait_for_available_methods(self, timeout: int | None = None) -> CheckoutDeliveryMethodsComponent:
        deadline = time.monotonic() + ((timeout or self.DEFAULT_TIMEOUT) / 1000)
        while time.monotonic() < deadline:
            if self.__list_container.first.is_visible() and self.__visible_tiles(self.__list_tiles):
                return self
            if self.__matrix_container.first.is_visible() and self.__visible_tiles(self.__matrix_tiles):
                return self
            self.root.page.wait_for_timeout(QUICK_PROBE_MS)

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

    def _get_methods_layout_ready(self) -> tuple[DeliveryMethodsLayout, list[str] | list[list[str]]]:
        if self.__list_container.first.is_visible():
            return DeliveryMethodsLayout.LIST, self.__get_available_methods_list()
        if self.__matrix_container.first.is_visible():
            return DeliveryMethodsLayout.MATRIX, self.__get_available_methods_matrix()
        raise RuntimeError("Nie udało się rozpoznać układu metod transportu.")

    def get_methods_layout(self) -> tuple[DeliveryMethodsLayout, list[str] | list[list[str]]]:
        self.wait_for_available_methods()
        return self._get_methods_layout_ready()

    def __available_tiles_for_layout(self, layout: DeliveryMethodsLayout) -> list[Locator]:
        if layout == DeliveryMethodsLayout.LIST:
            return self.__visible_tiles(self.__list_tiles)
        return self.__visible_tiles(self.__matrix_tiles)

    @step("Wybieram losową dostępną metodę transportu i przechodzę dalej")
    def choose_random_available_method(self, *, ensure_available: bool = True) -> DeliveryMethodsLayout:
        if ensure_available:
            self.wait_for_available_methods()
        layout, _ = self._get_methods_layout_ready()
        available_tiles = self.__available_tiles_for_layout(layout)

        if not available_tiles:
            raise RuntimeError("Brak dostępnych metod transportu do wyboru.")

        self.pointer_click(random.choice(available_tiles))
        return layout

    @step("Wybieram metodę transportu zawierającą tekst: {text}")
    def choose_method_containing(self, text: str, *, ensure_available: bool = True) -> DeliveryMethodsLayout:
        normalized_expected = " ".join(text.split()).casefold()
        if ensure_available:
            self.wait_for_available_methods()
        layout, _ = self._get_methods_layout_ready()
        for tile in self.__available_tiles_for_layout(layout):
            normalized_actual = self.__normalize_tile_text(tile).casefold()
            if normalized_expected in normalized_actual:
                self.pointer_click(tile)
                return layout

        raise RuntimeError(f"Nie znaleziono metody transportu zawierającej tekst: '{text}'.")
