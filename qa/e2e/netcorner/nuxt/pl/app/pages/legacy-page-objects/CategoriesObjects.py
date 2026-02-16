from urllib.parse import urljoin

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.Common.PageObjects.CommonProductListObjects import (
    CommonProductListObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CategoriesLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ProductListObject import (
    ProductListObject,
)

import settings


class NavigateToProductListByUrl(CommonPO):
    def __init__(self, driver):
        super().__init__(driver)


class CategoryTreeNavigator(CommonPO):
    def __init__(self, driver, traversal_path: dict):
        super().__init__(driver)

        self.locator = CategoriesLocators()
        self.traversal_path = traversal_path

    def __get_tile_links_status(self, tile_name: str) -> CommonPO.ListCommon[dict]:
        self.wait_for.element_visible(self.locator.ELEMENT_tile_box.format(tile_name))
        links_status = []
        tile_links = self.driver.locator(self.locator.ELEMENT_tile_links.format(tile_name))
        for idx in range(tile_links.count()):
            link = tile_links.nth(idx)
            href = link.get_attribute("href")
            if not href:
                continue
            links_status.append(
                {"name": link.inner_text(), "url": urljoin(self.driver.current_url, href)})
        return links_status

    def __hover_tile(self, tile_name: str):
        if not settings.is_session_headless:
            self.wait_for.element_visible(self.locator.ELEMENT_tile_box.format(tile_name)).hover()

    def traverse_tiles(self) -> list[list[str | bool]]:
        def parse_category(category: str) -> str | None:
            if category == "":
                return None
            return category

        def process_category_tile(category: str) -> str | str | tuple[str, CommonPO.ListCommon[dict]]:
            if category:
                self.scroll_to.element(self.wait_for.element_visible(self.locator.ELEMENT_tile_box.format(category)))
                self.__hover_tile(category)
                links = self.__get_tile_links_status(category)
                self.click_element(
                    self.wait_for.element_visible(self.locator.ELEMENT_tile_box.format(category)))
                return category, links

        category_first = parse_category(self.traversal_path["first_level"])
        category_second = parse_category(self.traversal_path["second_level"])
        category_third = parse_category(self.traversal_path["third_level"])

        self.wait_for.element_visible(
            self.locator.ELEMENT_category_root_from_header.format(self.traversal_path["root"])).click()

        categories = [process_category_tile(category_first),
                      process_category_tile(category_second),
                      process_category_tile(category_third)]

        product_lists_visible = []
        for category in categories:
            if category:
                for url in category[1]:
                    self.driver.get(url["url"])
                    product_lists_visible.append([url["url"], ProductListObject(self.driver).is_product_list_visible()])
        return product_lists_visible


class ListingFunctions(CommonProductListObjects):
    def __init__(self, driver):
        super().__init__(driver)
