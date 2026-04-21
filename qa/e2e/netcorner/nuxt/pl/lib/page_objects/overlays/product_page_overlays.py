from __future__ import annotations

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


def __wait_until_visible(self, timeout: int) -> bool:
        try:
            self.wait_visible(timeout=timeout)
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
        self.safe_click(self.__btn_continue_shopping)

    @step("Klikam 'Przejdź do koszyka' na warstwie dodawanie produktu do koszyka")
    def click_go_to_cart(self, overlay_timeout: int = 7_500) -> None:
        if not __wait_until_visible(self, overlay_timeout):
            return
        self.safe_click(self.__btn_go_to_cart)

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
            "role=button[name='Nie, dziękuję - chcę kupić tylko produkt']"
        )

    def get_proposed_promotions(self, overlay_timeout: int = 7_500) -> list[str]:
        if not __wait_until_visible(self, overlay_timeout):
            return []

        promotions: list[str] = []
        for index in range(self.__promotion_names.count()):
            text = self.__promotion_names.nth(index).inner_text().strip()
            if text:
                promotions.append(text)

        return list(dict.fromkeys(promotions))

    @step("Klikam 'Nie, dziękuję - chcę kupić tylko produkt' na warstwie promocji i zwracam listę promocji")
    def click_buy_only_product(self, overlay_timeout: int = 7_500) -> list[str]:
        promotions = self.get_proposed_promotions(overlay_timeout=overlay_timeout)
        if not promotions and not __wait_until_visible(self, timeout=0):
            return promotions
        self.safe_click(self.__button_buy_only_product)
        return promotions
