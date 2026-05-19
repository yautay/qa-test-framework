from __future__ import annotations

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


def _wait_until_visible(component: BaseComponent, timeout: int) -> bool:
    try:
        component.wait_visible(timeout=timeout)
        return True
    except (AssertionError, PlaywrightTimeoutError):
        return False


class ProductPageGoToCartOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(
            page.locator('[data-name="dialogContent"]:visible').filter(
                has=page.get_by_role("heading", name="Produkt dodany do koszyka")
            ),
            name="Add To Cart Overlay",
        )

        self.__btn_continue_shopping = self.find("role=button[name='Wróć do zakupów']")
        self.__btn_go_to_cart = self.find("role=button[name='Przejdź do koszyka']")

    @step("Klikam 'Wróć do zakupów' na warstwie dodawanie produktu do koszyka")
    def click_continue_shopping(self) -> None:
        self.pointer_click(self.__btn_continue_shopping)

    @step("Klikam 'Przejdź do koszyka' na warstwie dodawanie produktu do koszyka")
    def click_go_to_cart(self, overlay_timeout: int = 7_500) -> None:
        if not _wait_until_visible(self, overlay_timeout):
            return
        self.pointer_click(self.__btn_go_to_cart)


class ProductPagePromotionsOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(
            page.locator('[data-name="dialogContent"]:visible').filter(
                has=page.get_by_role("heading", name="Ten produkt możesz kupić w promocji")
            ),
            name="Product Promotions Overlay",
        )

        self.__promotion_names = self.find(".swiper-slide-visible .pagination-text")
        self.__button_buy_only_product = self.find(
            "role=button[name=/^(Nie, dziękuję - chcę kupić tylko produkt|Przejdź dalej)$/]"
        )

    def get_proposed_promotions(self, overlay_timeout: int = 7_500) -> list[str]:
        if not _wait_until_visible(self, overlay_timeout):
            return []

        promotions: list[str] = []
        for index in range(self.__promotion_names.count()):
            text = self.__promotion_names.nth(index).inner_text().strip()
            if text:
                promotions.append(text)

        return list(dict.fromkeys(promotions))

    @step("Klikam 'Nie, dziękuję - chcę kupić tylko produkt' na warstwie promocji i zwracam listę promocji")
    def click_buy_only_product(self, overlay_timeout: int = 7_500) -> list[str]:
        if not _wait_until_visible(self, overlay_timeout):
            return []
        promotions = self.get_proposed_promotions(overlay_timeout=overlay_timeout)
        self.pointer_click(self.__button_buy_only_product)
        return promotions


class ProductPageWishlistOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(
            page.locator('[data-name="dialogContent"]:visible'),
            name="Product Wishlist Overlay",
        )

        self.__wishlist_checkboxes = self.find("[id^='checkboxWishlistAdd-']")
        self.__create_new_list_button = self.find("button").filter(has_text="Utwórz nową listę")
        self.__add_to_selected_button = self.find("button").filter(has_text="Dodaj do wybranej")
        self.__wishlist_name_input = self.find("#wishlistInput")
        self.__create_wishlist_button = self.find("button").filter(has_text="Utwórz listę")
        self.__go_to_wishlist_button = self.find("role=button[name='Przejdź do listy życzeń']")

    def __resolve_wishlist_checkbox(self, wishlist_name: str | None = None) -> Locator:
        if wishlist_name:
            return self.find(f"#checkboxWishlistAdd-{wishlist_name}")
        return self.__wishlist_checkboxes.first

    @step("Ustawiam stan checkboxa na liście życzeń")
    def set_wishlist_checkbox_state(
        self,
        checked: bool,
        wishlist_name: str | None = None,
        overlay_timeout: int = 7_500,
    ) -> None:
        if not _wait_until_visible(self, overlay_timeout):
            return
        checkbox = self.__resolve_wishlist_checkbox(wishlist_name)
        if checked:
            checkbox.check()
        else:
            checkbox.uncheck()

    @step("Klikam 'Utwórz nową listę'")
    def click_create_new_list(self, overlay_timeout: int = 7_500) -> None:
        if not _wait_until_visible(self, overlay_timeout):
            return
        self.pointer_click(self.__create_new_list_button)

    @step("Klikam 'Dodaj do wybranej'")
    def click_add_to_selected(self, overlay_timeout: int = 7_500) -> None:
        if not _wait_until_visible(self, overlay_timeout):
            return
        self.pointer_click(self.__add_to_selected_button)

    @step("Wpisuję nazwę listy życzeń")
    def enter_wishlist_name(self, value: str, overlay_timeout: int = 7_500) -> None:
        if not _wait_until_visible(self, overlay_timeout):
            return
        self.safe_type(self.__wishlist_name_input, value)

    @step("Klikam przycisk Utwórz listę")
    def click_create_wishlist(self, overlay_timeout: int = 7_500) -> None:
        if not _wait_until_visible(self, overlay_timeout):
            return
        self.pointer_click(self.__create_wishlist_button)

    @step("Klikam 'Przejdź do listy życzeń'")
    def go_to_wishlist(self, overlay_timeout: int = 7_500) -> None:
        if not _wait_until_visible(self, overlay_timeout):
            return
        self.pointer_click(self.__go_to_wishlist_button)
