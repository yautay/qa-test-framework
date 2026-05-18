from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class WishlistListItem(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="Wishlist List Item")

        self.__wishlist_name = self.find("h3")
        self.__remove_wishlist_button = self.find("button").filter(has_text="Usuń listę")
        self.__product_link = self.find("a.line-clamp-3.font-medium")
        self.__remove_product_icon = self.find("button i.i-trash-square")

    @step("Klikam w link produktu")
    def click_product_link(self) -> None:
        self.pointer_click(self.__product_link)

    @step("Klikam w ikonę usunięcia produktu z listy")
    def click_remove_product_icon(self) -> None:
        self.pointer_click(self.__remove_product_icon)

    @step("Klikam w przycisk Usuń listę")
    def click_remove_wishlist_button(self) -> None:
        self.pointer_click(self.__remove_wishlist_button)

    @step("Pobieram nazwę listy życzeń")
    def get_wishlist_name(self) -> str:
        return (self.__wishlist_name.first.text_content() or "").strip()

    @step("Pobieram nazwę produktu")
    def get_product_name(self) -> str:
        return (self.__product_link.first.text_content() or "").strip()


class WishlistComponent(BaseComponent):
    ROOT_SELECTOR = "#pageContent"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Wishlist Component")
        self.__wishlist_elements = self.root.locator(
            "xpath=.//div[.//h3 and .//button[contains(normalize-space(.), 'Usuń listę')]]"
        )

    @staticmethod
    def __normalize_name(value: str) -> str:
        return " ".join(value.strip().lower().replace("_", " ").split())

    def count(self) -> int:
        return self.__wishlist_elements.count()

    def item(self, index: int) -> WishlistListItem:
        return WishlistListItem(self.__wishlist_elements.nth(index))

    def items(self) -> list[WishlistListItem]:
        return [self.item(index) for index in range(self.count())]

    @step("Wyszukuję listę życzeń po nazwie: {wishlist_name}")
    def find_by_name(self, wishlist_name: str, timeout: int = 7500) -> WishlistListItem | None:
        expected_name = self.__normalize_name(wishlist_name)
        attempts = max(1, timeout // 250)

        for _ in range(attempts):
            for element in self.items():
                actual_name = self.__normalize_name(element.get_wishlist_name())
                if actual_name == expected_name or expected_name in actual_name:
                    return element
        return None

