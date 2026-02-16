import random

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    HomePageLocators,
    HomePageOzoBoxLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects import (
    LayerWithProductRecommendationPageObjects,
)


class HomePageObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)
        self.locator = HomePageLocators()

    def get_ozo_details(self) -> dict | None:
        if self.is_ozo_visible():
            self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_current_price, timeout=self.TIMEOUT_MEDIUM)
            badge = self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_promo_badge, raise_exception=False)
            if badge:
                badge = True
            title = self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_title).text
            price = int(self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_current_price).text.strip(" zł"))
            previous_price = int(self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_original_price).text.strip(
                " zł"))
            omnibus_price = self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_lowest_price,
                                                          raise_exception=False)
            if omnibus_price:
                omnibus_price = int(omnibus_price.text.strip(" zł"))
            days_left = int(self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_countdown_days).text)
            sold_amount = int(self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_sold_amount).text)
            remaining_amount = int(self.wait_for.element_visible(HomePageOzoBoxLocators.ELEMENT_remaining_amount).text)

            return {
                "badge": badge,
                "title": title,
                "price": price,
                "previous_price": previous_price,
                "omnibus_price": omnibus_price,
                "days_left": days_left,
                "sold_amount": sold_amount,
                "remaining_amount": remaining_amount
            }
        return None

    def is_ozo_visible(self) -> bool:
        return self.wait_for.element_visible(
            HomePageLocators.CONTAINER_ozo_box,
            raise_exception=False,
            timeout=self.TIMEOUT_SHORT,
        ) is not None

    def verify_homepage_banners(self):
        for element, message in [
            (self.locator.CONTAINER_banners, "Banners container is not visible!"),
            (self.locator.ELEMENT_banners_thumb_navigator, "Banners navigator is not visible!")
        ]:
            self.wait_for.element_visible(element, message)

    def verify_products_container(self) -> bool:
        elements = self.driver.locator(self.locator.CHECKBOX_new_products).all_inner_texts()
        if any(elem.strip() == "Najnowsze produkty" for elem in elements):
            self.count_not_hidden_products()
            promotions = self.wait_for.element_visible(
                self.locator.CONTAINER_our_promotions, "Our promotions section is not visible!"
            )
            assert promotions.text == "Promocje", "There is no section name in our promotions container"
            return True

        raise AssertionError("There is no section name in new products container")

    def count_not_hidden_products(self):
        not_hidden_products = self.driver.locator(HomePageLocators.ELEMENT_new_products_not_hidden_products).count()
        assert not_hidden_products != 0, "There is no product in new section!"

    def select_product_from_new_products_box(self):
        self.wait_for.element_visible(HomePageLocators.CONTAINER_daily_deal)
        daily_deal_products = self.driver.locator(HomePageLocators.ELEMENTS_daily_deal_product_tiles)
        visible_indexes = []
        for idx in range(daily_deal_products.count()):
            if daily_deal_products.nth(idx).is_visible():
                visible_indexes.append(idx)
        if not visible_indexes:
            raise AssertionError("No visible daily deal products found")
        daily_deal_products.nth(random.choice(visible_indexes)).click()
        LayerWithProductRecommendationPageObjects(self.driver).skip_recommendation_layer_if_visible()
