import enum
import math
import random
import re
from urllib.parse import urljoin

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    FilterLocators,
    ProductListLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.LayersObjects import (
    LayerProductsAddedToCompareObjects,
    LayerPromotionsObject,
    LayerSummaryObject,
    LayerWithProductRecommendationPageObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ProductPageObjects import (
    ProductPageObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ToastsObjects import (
    ToastsObjects,
)
from TestData.pl_komputronik_nuxt.data_sorting_product_list import sort_options
from TestData.pl_komputronik_nuxt.PlCommonKeys import ProductAvailabilityKey, ToastTypeKey


class ProductListObject(CommonPO):
    def __init__(self, driver):
        super().__init__(driver)

    def is_product_list_visible(self) -> bool:
        return self.wait_for.element_visible(ProductListLocators.CONTAINER_products_list, raise_exception=False)

    def exclude_unavailable_products(self):
        checkbox = self.wait_for.element_visible(ProductListLocators.ELEMENT_checkbox_show_unavailable,
                                                 timeout=self.TIMEOUT_LONG,
                                                 raise_exception=False)
        if checkbox and checkbox.get_attribute("checked"):
            checkbox.click(self.TIMEOUT_SHORT)

    def get_pagination_number(self) -> int:
        pagination_tail = self.wait_for.element_visible(ProductListLocators.ELEMENT_pagination_last_page,
                                                                raise_exception=False)
        if pagination_tail:
            return int(self.wait_for.element_visible(ProductListLocators.ELEMENT_pagination_last_page).text)
        return 0

    def get_products_count(self) -> int:
        if self.wait_for.element_visible(ProductListLocators.ELEMENT_products_count, raise_exception=False):
            return int(re.search(
                r'\d+', self.wait_for.element_visible(ProductListLocators.ELEMENT_products_count).text).group())
        return 0

    def get_erp_codes_from_listing(self) -> [str]:
        self.wait_for.element_visible(ProductListLocators.ELEMENTS_erp_codes)
        erp_codes = []
        for code in self.driver.locator(ProductListLocators.ELEMENTS_erp_codes).all_inner_texts():
            parts = code.split("Kod systemowy: ")
            if len(parts) > 1:
                erp_codes.append(parts[1])
        return erp_codes

    def get_products_urls_form_listing(self) -> CommonPO.ListCommon[str]:
        products_urls = []
        self.time.sleep(self.TIMEOUT_SHORT)
        product_links = self.driver.locator(ProductListLocators.ELEMENT_product_webelement_link)
        for idx in range(product_links.count()):
            href = product_links.nth(idx).get_attribute("href")
            if not href:
                continue
            absolute_href = urljoin(self.driver.current_url, href)
            if "/product/" not in absolute_href and "/p/" not in absolute_href:
                continue
            products_urls.append(absolute_href)
        return products_urls

    def select_product_from_listing(self):
        self.wait_for.element_visible(ProductListLocators.BUTTONS_add_to_cart)
        buttons = self.driver.locator(ProductListLocators.BUTTONS_add_to_cart)
        for button_idx in range(buttons.count()):
            buttons.nth(button_idx).click()
            if not ToastsObjects(self.driver).get_toast() == ToastTypeKey.LIMITED_SALE_EXCEEDED:
                break
            else:
                self.time.sleep(self.TIMEOUT_MEDIUM)

    def get_products_names(self) -> CommonPO.ListCommon[str]:
        self.wait_for.element_visible(ProductListLocators.CONTAINER_products_list)
        self.time.sleep(self.TIMEOUT_NUXT_TOASTS)
        return self.driver.locator(ProductListLocators.ELEMENT_product_name).all_inner_texts()


class SelectTestProductFromProductListObject(ProductListObject):
    """
    Must be obtained from the Product Card, as not all data is available from the listing (e.g., Limited Sales).
    """

    def __init__(self, driver):
        super().__init__(driver)
        self.callable_data = None

    def get_product_from_listing_by_attribute(
            self, attribute: ProductAvailabilityKey = ProductAvailabilityKey.AVAILABLE) \
            -> CommonPO.WebElementCommon | bool:
        def __get_product() -> CommonPO.WebElementCommon:
            self.time.sleep(self.TIMEOUT_SHORT)
            if self.wait_for.element_visible(
                    ProductListLocators.ELEMENTS_products_by_attribute.format(attribute=attribute.value),
                    timeout=self.TIMEOUT_SHORT,
                    raise_exception=False):
                return self.get_webelement_instance(
                    ProductListLocators.ELEMENTS_products_by_attribute.format(attribute=attribute.value)
                )

        while not __get_product():
            if self.wait_for.element_visible(ProductListLocators.ELEMENT_next_pagination_page, raise_exception=False):
                self.scroll_to.element(
                    self.wait_for.element_visible(ProductListLocators.ELEMENT_next_pagination_page))
                self.click_element(
                    self.wait_for.element_visible(ProductListLocators.ELEMENT_next_pagination_page))
            else:
                return False
        return __get_product()

    def get_test_product(self, with_lift: bool = False, digital: bool = False, temporarily_unavailable: bool = False,
                         filters: dict = None, add_to_cart: bool = True,
                         product_page_function: CommonPO.CallableCommon = None) -> dict or None:
        def __product_is_test_friendly() -> bool:
            product_page_objects = ProductPageObjects(self.driver)
            self.wait_for.element_visible(
                ProductListLocators.MAIN_CONTAINER_product_list,
                timeout=self.TIMEOUT_SHORT,
                raise_exception=False,
            )
            if temporarily_unavailable:
                if product_page_objects.get_temporarily_unavailable_status():
                    return True
            else:
                if with_lift:
                    if (product_page_objects.get_lift_service_available_status()
                            and not product_page_objects.get_limited_sale_status()
                            and not product_page_objects.get_outlet_status()):
                        return True
                    return False
                elif digital:
                    if (product_page_objects.get_availability_status_digital_licence()
                            and not product_page_objects.get_limited_sale_status()
                            and not product_page_objects.get_outlet_status()):
                        return True
                    return False
                else:
                    if (product_page_objects.get_availability_status_3210()
                            and not product_page_objects.get_limited_sale_status()
                            and not product_page_objects.get_outlet_status()):
                        return True
                    return False

        def __get_products_urls() -> CommonPO.ListCommon[str]:
            urls = []
            products_url_locator = self.driver.locator(ProductListLocators.ELEMENTS_products_url)
            if products_url_locator.count() == 0:
                products_url_locator = self.driver.locator(ProductListLocators.ELEMENT_product_webelement_link)
            for idx in range(products_url_locator.count()):
                href = products_url_locator.nth(idx).get_attribute("href")
                if href and ("/product/" in href or "/p/" in href):
                    urls.append(urljoin(self.driver.current_url, href))
            return urls

        def __set_product_filters():
            FilterProductsList(self.driver).set_filters(filters)

        def __get_product() -> dict | bool:
            return_data = None
            if product_page_function:
                return_data = product_page_function()
            if add_to_cart:
                ProductPageObjects(self.driver).action_click_add_to_cart()
                LayerPromotionsObject(self.driver).close_layer_if_visible()
                LayerSummaryObject(self.driver).click_go_to_cart(timeout=self.TIMEOUT_LONG)
            return return_data

        def __iterate_products() -> bool or dict:
            products_urls = __get_products_urls()
            for product_url in products_urls:
                self.driver.get(product_url)
                if __product_is_test_friendly():
                    LayerWithProductRecommendationPageObjects(self.driver).skip_recommendation_layer_if_visible()
                    self.callable_data = __get_product()
                    return True
            return False

        if not temporarily_unavailable:
            self.exclude_unavailable_products()
        if filters:
            __set_product_filters()

        for _ in range(3):
            self.wait_for.element_visible(ProductListLocators.CONTAINER_products_list,
                                          timeout=self.TIMEOUT_LONG,
                                          raise_exception=False)
            if __get_products_urls() or self.wait_for.element_visible(
                ProductListLocators.BUTTONS_add_to_cart,
                timeout=2,
                raise_exception=False,
            ):
                break
            self.driver.refresh()
            self.time.sleep(1)

        tmp_url = self.driver.current_url
        while not __iterate_products():
            self.driver.get(tmp_url)
            next_page_button = self.wait_for.element_visible(
                ProductListLocators.ELEMENT_next_pagination_page,
                raise_exception=False,
            )
            if not next_page_button:
                fallback_products = __get_products_urls()
                if fallback_products:
                    self.driver.get(fallback_products[0])
                    LayerWithProductRecommendationPageObjects(self.driver).skip_recommendation_layer_if_visible()
                    self.callable_data = __get_product()
                    return self.callable_data

                self.select_product_from_listing()
                LayerPromotionsObject(self.driver).close_layer_if_visible()
                LayerSummaryObject(self.driver).click_go_to_cart(timeout=self.TIMEOUT_LONG)
                return self.callable_data

            next_page_button.click()
            tmp_url = self.driver.current_url
        return self.callable_data


class ProductListSort(ProductListObject):
    def __init__(self, driver, sort_type: str):
        super().__init__(driver)
        self.sort_type = self.validate_sort_type(sort_type)
        self.sort_option = sort_options[self.sort_type]

    def validate_sort_type(self, sort_type: str) -> str:
        return self.param_has_expected_value(
            sort_type, ("price_ascending", "price_descending", "name_ascending", "name_descending"))

    def sort_product_list(self):
        """Sorts the product list using the selected sort_type."""
        self.click_sort_option(self.sort_option)
        self.wait_for.element_visible(ProductListLocators.DROPDOWN_sorting_menu)

    def assert_sorting(self):
        """Asserts sorted product list."""
        self.wait_for.element_visible(ProductListLocators.CONTAINER_products_list)
        page_sorted_data = self.get_page_sorted_data()

        # Sorts gathered data ascending or descending depending on sorting type.
        py_sorted_data = sorted(page_sorted_data) if "ascending" in self.sort_type \
            else sorted(page_sorted_data, reverse=True)

        msg = f"Sort option '{self.sort_option}' is incorrect!"

        # Tries to assert gathered (and sorted) data with data from the page.
        if py_sorted_data == page_sorted_data:
            pass
        else:
            for py_data, page_data in zip(py_sorted_data, page_sorted_data):
                status = "OK" if py_data == page_data else "FAIL"
                print(f"{status:5} {py_data} -- {page_data}")

            raise AssertionError(msg)

    def get_page_sorted_data(self) -> CommonPO.ListCommon[CommonPO.UnionCommon[float, str]]:
        """Gathers products prices or names depending on the sorting type."""
        self.time.sleep(self.TIMEOUT_SHORT)
        if self.sort_type in ("price_ascending", "price_descending"):
            self.time.sleep(self.TIMEOUT_SHORT)
            prices = []
            for raw_price in self.driver.locator(ProductListLocators.ELEMENT_product_price).all_inner_texts():
                normalized = re.sub("[^0-9.]", "", raw_price.replace(",", "."))
                if normalized:
                    prices.append(float(normalized))
            return prices
        else:
            self.time.sleep(self.TIMEOUT_SHORT)
            return [name.lower() for name in self.driver.locator(ProductListLocators.ELEMENT_product_name).all_inner_texts()]

    def click_sort_option(self, option: str):
        """Clicks the drop-down menu to open it and selects the given option."""
        sort_drop_down_locator = self.wait_for.element_visible(ProductListLocators.DROPDOWN_sorting_menu)
        sort_drop_down_locator.click()

        option_locator = ProductListLocators.BUTTON_sort_option.format(option)
        self.wait_for.element_visible(option_locator).click()


class ProductListAddProductToCompare(ProductListObject):
    def __init__(self, driver):
        super().__init__(driver)

    def add_random_products_to_compare(self):
        self.time.sleep(self.TIMEOUT_NUXT_TOASTS)
        buttons = self.driver.locator(ProductListLocators.BUTTONS_add_to_compare)
        total_buttons = buttons.count()
        if total_buttons == 0:
            raise AssertionError("No add-to-compare checkboxes found")

        sample_size = min(3, total_buttons)
        sampled_indexes = random.sample(range(total_buttons), sample_size)
        for button_idx, sampled_index in enumerate(sampled_indexes):
            add_to_compare_btn = buttons.nth(sampled_index)
            if add_to_compare_btn.is_visible():
                add_to_compare_btn.scroll_into_view_if_needed()
                add_to_compare_btn.click()
            if button_idx < len(sampled_indexes) - 1:
                LayerProductsAddedToCompareObjects(self.driver).close_layer()


class FilterProductsList(ProductListObject):
    def __init__(self, driver):
        super().__init__(driver)

    def set_filters(self, filters: dict[enum: str]):
        for k, v in filters.items():
            filter_web_element = self.wait_for.element_visible(
                FilterLocators.CONTAINER_filter_type.format(filter_data_type=k.value), raise_exception=False)
            unwind_container = self.wait_for.element_visible(
                FilterLocators.CONTAINER_filter_type.format(filter_data_type=k.value) +
                FilterLocators.ELEMENTS_unroll_all_filters, raise_exception=False)
            self.click_element(unwind_container) if unwind_container else ...
            self.scroll_to.element(filter_web_element)
            self.time.sleep(self.TIMEOUT_SHORT)
            filter_type = filter_web_element.get_attribute("data-filter-type")
            match filter_type:
                case "checkbox":
                    for element in v:
                        self.wait_for.element_visible(
                            FilterLocators.CONTAINER_filter_type.format(filter_data_type=k.value) +
                            FilterLocators.INPUT_checkbox.format(filter_value=element)).click(self.TIMEOUT_NUXT_TOASTS)
                case "input":
                    inputs_locator = self.driver.locator(
                        FilterLocators.CONTAINER_filter_type.format(filter_data_type=k.value)
                        + FilterLocators.INPUT_number
                    )
                    for element_order, element_value in enumerate(v):
                        if element_order >= inputs_locator.count():
                            break
                        inputs_locator.nth(element_order).fill(str(element_value))
                        self.time.sleep(self.TIMEOUT_NUXT_TOASTS)

    def get_active_filters(self) -> CommonPO.ListCommon[str]:
        self.wait_for.element_visible(FilterLocators.CONTAINER_active_filters)
        self.time.sleep(self.TIMEOUT_NUXT_TOASTS)
        return self.driver.locator(FilterLocators.ELEMENTS_active_filters).all_inner_texts()


class ProductListPaginationObjects(ProductListObject):
    def __init__(self, driver):
        super().__init__(driver)

    @staticmethod
    def get_pagination(products_number: int, products_per_page: int = 20) -> int:
        if products_number > products_per_page:
            return math.ceil(products_number / products_per_page)
        return 0

    @staticmethod
    def get_pagination_urls(base_listing_url: str, pagination_count: int, random_elements: int = 0) -> \
    CommonPO.ListCommon[str]:
        url_template = "{base}?showBuyActiveOnly=1&p={page}"
        pagination_urls = []
        if random_elements >= pagination_count or random_elements == 0:
            index = random.sample(range(1, pagination_count + 1), k=pagination_count)
        else:
            index = random.sample(range(1, pagination_count + 1), k=random_elements)
        for element in index:
            pagination_urls.append(url_template.format(base=base_listing_url, page=element))
        return pagination_urls

    def get_pagination_content_data(self, pagination_urls: CommonPO.ListCommon[str]) -> CommonPO.ListCommon[dict]:
        products_data = []
        for url in pagination_urls:
            self.driver.get(url)
            self.time.sleep(self.TIMEOUT_SHORT)
            products_data += ProductPageObjects(self.driver).get_product_data(
                products_urls=self.get_products_urls_form_listing())
        return products_data
