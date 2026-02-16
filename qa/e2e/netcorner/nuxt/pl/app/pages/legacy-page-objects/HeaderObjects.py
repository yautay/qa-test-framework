from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    HeaderLocators,
    MyAccountLocators,
    SearchLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ToastsObjects import (
    ToastsObjects,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import ToastTypeKey


class HeaderObjects(CommonPO):
    def __init__(self, driver, check_element_in_object: CommonPO.AnyCommon | None = None):
        super().__init__(driver)
        self._is_element_in_object = check_element_in_object
        self.locator = HeaderLocators()
        self.search_locator = SearchLocators()

    def go_to_homepage(self):
        self.wait_for.element_visible(self.locator.ELEMENT_logo).click()

    def verify_visibility_of_header_elements(self, test_case: str):
        elements_to_check = {
            "header_elements": [
                self.locator.CONTAINER_header,
                self.locator.ELEMENT_logo,
                self.locator.ELEMENT_help_and_contact,
                self.locator.ELEMENT_login,
                self.locator.DROP_DOWN_lvl_zero,
                self.locator.LINK_cart,
                self.locator.ELEMENT_phone_number,
            ],
            "search_by_codes": [
                self.search_locator.INPUT_search,
                self.search_locator.BUTTON_search,
            ]
        }

        elements = elements_to_check.get(test_case, [])
        for element in elements:
            self.wait_for.element_visible(element)

    def assert_zero_level_categories(self, test_data):
        """
            Using variable '_is_element_in_object' a Selenium method 'assertIn' from unittest package is called.
            This method checks if zero-level categories from main page actually are placed properly in an object.
            In other words - it is checked if text acquired from main page (variable 'c' in for loop) is the same as
            in the predefined TestData dictionary 'categories_in_header'.
        """
        categories_all_elements = self.driver.locator(self.locator.DROP_DOWN_all_elements).all_inner_texts()
        next(self._is_element_in_object(c, test_data["categories_in_header"]) for c in categories_all_elements)

    def assert_current_selected_search_category(self):
        current_search_category = self.driver.locator(
            self.locator.ELEMENT_search_where_current_selected_category).first.inner_text()
        assert current_search_category == "wszędzie", (f"Wrong current selected category, should be 'wszędzie',"
                                                       f" but was '{current_search_category}'.")

    def assert_search_categories(self, test_data):
        self.wait_for.element_visible(self.locator.ELEMENT_search_where).click()

        search_categories_items = self.driver.locator(self.locator.LIST_search_where).all_inner_texts()
        expected_categories = test_data["categories_in_header"]

        for item in search_categories_items:
            assert item in expected_categories, f"'{item}' not found in {expected_categories}"

    def assert_and_click_search_element(self):
        self.wait_for.element_visible(self.locator.ELEMENT_search_where,
                                      "Search 'where' dropdown is not visible!").click()
        self.element_attribute.attribute_has_value(self.locator.ELEMENT_search_where, "data-name",
                                                   "searchCategoryWrapper")

    def assert_header_links(self):
        help_and_contact = self.wait_for.element_visible(
            self.locator.ELEMENT_help_and_contact,
            "Help/contact menu trigger is not visible!",
            raise_exception=False,
        )
        if help_and_contact:
            try:
                help_and_contact.hover()
            except Exception:
                pass

        links = {
            "store": (self.locator.LINK_find_store, "/storehouse/find"),
            "contact": (self.locator.LINK_find_contact, "/informacje/kontakt/"),
            "complaint": (self.locator.LINK_find_complaint, "/informacje/pomoc/reklamacje/"),
            "return": (self.locator.LINK_find_return, "/informacje/pomoc/zwroty/"),
            "shipping": (self.locator.LINK_find_shipping, "/informacje/pomoc/dostawa/")
        }

        for name, (locator, href) in links.items():
            link = self.wait_for.element_visible(
                locator,
                f"{name.capitalize()} link is not visible!",
                raise_exception=False,
                timeout=self.TIMEOUT_SHORT,
            )
            if not link:
                link = self.get_webelement_instance(locator)
            assert link.get_attribute("href") == href

    def enter_my_account(self):
        if self.wait_for.element_visible(HeaderLocators.ELEMENT_your_account, raise_exception=False):
            self.click_element(self.wait_for.element_visible(HeaderLocators.ELEMENT_your_account))

    def enter_login_layer(self):
        if self.wait_for.element_visible(HeaderLocators.ELEMENT_login, raise_exception=False):
            self.click_element(self.wait_for.element_visible(HeaderLocators.ELEMENT_login))

    def logout_user(self) -> None | ToastTypeKey:
        self.enter_my_account()
        self.click_element(self.wait_for.element_visible(MyAccountLocators.BUTTON_logout_user))
        return ToastsObjects(self.driver).get_toast()

    def go_to_cart(self):
        self.wait_for.element_visible(HeaderLocators.ELEMENT_cart).click(self.TIMEOUT_SHORT)

    def get_login_status(self) -> bool:
        login_btn = self.wait_for.element_visible(HeaderLocators.ELEMENT_login, timeout=self.TIMEOUT_SHORT,
                                                  raise_exception=False)
        my_account_btn = self.wait_for.element_visible(HeaderLocators.ELEMENT_your_account, timeout=self.TIMEOUT_SHORT,
                                                       raise_exception=False)
        if my_account_btn:
            my_account_btn = my_account_btn.is_displayed()
        if login_btn:
            login_btn = login_btn.is_displayed()
        if my_account_btn:
            return True
        if login_btn:
            return False
