import random

from TestCases.NetCornerProducts.Common.PageLocators.CommonAdminLocators import CommonAdminLocators
from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.AggregatorLocators import (
    AggregatorLocators,
)


class AggregatorObjects(CommonBasePageObject):

    def __init__(self, driver):
        super().__init__(driver)

        self.locator = AggregatorLocators()
        self.common_locator = CommonAdminLocators()

    def select_random_product(self):
        products = self.driver.locator(self.locator.ELEMENT_agregator_product)
        products_count = products.count()
        if products_count == 0:
            raise TimeoutError("No aggregator products found")

        random_product = products.nth(random.randrange(products_count))
        random_product.hover()

        product_buttons = random_product.locator(f"xpath={self.locator.BUTTON_buy_product_in_card}")
        for idx in range(product_buttons.count()):
            button = product_buttons.nth(idx)
            if button.is_visible() and button.is_enabled():
                button.click()
                return

        fallback_buttons = self.driver.locator(self.locator.BUTTON_buy_product)
        for idx in range(fallback_buttons.count()):
            button = fallback_buttons.nth(idx)
            if button.is_visible() and button.is_enabled():
                button.click()
                return

        raise TimeoutError("No visible enabled 'Sprawdź' button found on aggregator card")

    def aggregator_visibility(self, test_data: dict, base_url: str) -> bool:
        self.driver.get(base_url + f"promocje/{test_data['aggregator_data']['url']}")
        return self.wait_for.element_visible(self.locator.HEADER_aggregator, raise_exception=False) is not None

    def add_random_product_form_aggregator(self):
        products = self.driver.locator(self.locator.COMPONENT_aggregator_product)
        products_count = products.count()
        if products_count == 0:
            raise TimeoutError("No aggregator products found")
        products.nth(random.randrange(products_count)).click()
