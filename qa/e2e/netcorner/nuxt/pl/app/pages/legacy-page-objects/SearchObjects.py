from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import SearchLocators


class SearchObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def search_phrase(self, phrase: str, category: str | None = None):
        self.fill_search_input(phrase)
        if category:
            self.__select_category(category)
        self.__click_search_button()

    def fill_search_input(self, search_phrase: str):
        self.time.sleep(self.TIMEOUT_SHORT)
        self.send_keys(self.wait_for.element_visible(SearchLocators.INPUT_search), search_phrase)

    def __select_category(self, category: str):
        self.wait_for.element_visible(SearchLocators.DROPDOWN_search_category).click()
        self.wait_for.element_visible(SearchLocators.SELECT_search_category.format(category=category)).click()

    def __click_search_button(self):
        self.wait_for.element_visible(SearchLocators.BUTTON_search).click()


class SearchSuggestion(SearchObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def verify_suggester(self, search_phrase: str, is_producer: bool = False):
        self.fill_search_input(search_phrase)
        assert self.wait_for.element_visible(SearchLocators.SECTION_products)
        assert self.wait_for.element_visible(SearchLocators.SECTION_producer)
        self.__assert_products_section(search_phrase=search_phrase, is_producer=is_producer)
        if is_producer:
            self.__assert_producer_section(search_phrase=search_phrase)

    def __assert_products_section(self, search_phrase: str, is_producer: bool):
        products_list = self.driver.locator(SearchLocators.ELEMENTS_products).all_inner_texts()
        if len(products_list) > 6:
            raise Exception("The page is rather excessively populated with products.")

        # Asserts products name
        if is_producer:
            for product in products_list:
                assert search_phrase.lower() in product.lower()

    def __assert_producer_section(self, search_phrase: str):
        producer_url = self.driver.locator(SearchLocators.ELEMENT_producer).first.get_attribute("href") or ""
        assert search_phrase in producer_url
