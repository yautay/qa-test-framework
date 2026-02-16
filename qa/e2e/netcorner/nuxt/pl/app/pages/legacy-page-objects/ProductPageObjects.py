from __future__ import annotations

import random
import re
from unittest import TestCase

from Lib.Actions.playwright_element import PlaywrightWebElement
from TestCases.NetCornerProducts.Common.PageObjects.CommonProductPageObjects import (
    CommonProductPageObjects as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    ProductOpinionPageLocators,
    ProductPageLocators,
    ProductPagePriceContainerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects import LayerSummaryObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.LayersObjects import (
    LayerWithProductNewsletter,
    LayerWithProductRecommendationPageObjects,
    LayerWithStorehouseAvailability,
)
from TestData.CommonData.data_search_listings import breadcrumbs_exceptions, maker_exceptions
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import ProductPageAlertKey


class ProductPageObjects(CommonPO):
    def __init__(self, driver):
        super().__init__(driver, ProductPageLocators())

    def sign_to_newsletter(self, email: str):
        self.wait_for.element_visible(self.locator.ELEMENT_sign_to_newsletter)
        buttons = self.driver.locator(self.locator.ELEMENT_sign_to_newsletter)
        for idx in range(buttons.count()):
            button = buttons.nth(idx)
            if button.is_visible():
                button.click()
        LayerWithProductNewsletter(self.driver).sign_to_newsletter(email)

    def add_product_to_cart_by_product_id(self, test_class: TestCase, product_id: int):
        self.driver.get(test_class.base_url + f"product/{str(product_id)}")
        self.click_element(self.get_add_to_cart_button())
        LayerSummaryObject(self.driver).click_go_to_cart(timeout=self.TIMEOUT_LONG)

    def get_add_to_cart_button(self, omit_button: bool = False,
                               enter_cart: bool = False) -> CommonPO.WebElementCommon or bool:
        self.wait_for.element_visible(self.locator.ELEMENT_product_name, timeout=self.TIMEOUT_LONG)
        if not omit_button:
            self.wait_for.element_visible(self.locator.BUTTON_add_to_cart, timeout=self.TIMEOUT_SHORT,
                                                  raise_exception=False)
        buttons = self.driver.locator(self.locator.BUTTON_add_to_cart)
        for idx in range(buttons.count()):
            button = buttons.nth(idx)
            button_element = PlaywrightWebElement(button)
            if self.wait_for.element_visible(button_element, raise_exception=False, timeout=self.TIMEOUT_SHORT):
                self.wait_for_attribute_disappear(button_element)
                if button.get_attribute("disabled"):
                    return False
                if enter_cart:
                    button.click()
                return button_element

    def get_product_name(self) -> str:
        return self.wait_for.element_visible(self.locator.ELEMENT_product_name).text

    def get_product_id(self) -> str:
        content = self.driver.locator(ProductPageLocators.META_info_product_id).first.get_attribute("content")
        return content or ""

    def get_product_erp_code(self) -> str:
        self.wait_for.element_visible(self.locator.ELEMENT_product_name)
        erp_codes = self.driver.locator(self.locator.ELEMENT_product_erp_code)
        for idx in range(erp_codes.count()):
            code = erp_codes.nth(idx)
            if code.is_visible():
                return code.inner_text().replace("Kod systemowy: ", "")
        return ""

    def get_storehouses_availability(self) -> list[list[str]]:
        if self.wait_for.element_visible(self.locator.ELEMENT_storehouses_availability_note,
                                         raise_exception=False):
            self.wait_for.element_visible(self.locator.ELEMENT_storehouses_availability_details).click()
            return LayerWithStorehouseAvailability(self.driver).get_storehouses_availability_details()

    def get_availability_status(self) -> str:
        product_page_status = self.wait_for.element_visible(self.locator.ELEMENT_product_availability_status,
                                                            raise_exception=False)
        if product_page_status:
            product_page_status = self.wait_for.element_visible(self.locator.ELEMENT_product_availability_status).text
        if self.wait_for.element_visible(self.locator.ELEMENT_product_availability_status_subtitle,
                                         raise_exception=False):
            description = self.wait_for.element_visible(self.locator.ELEMENT_product_availability_status_subtitle).text
            product_page_status = product_page_status + " " + description
        return product_page_status

    def get_availability_status_3210(self) -> bool:
        if PlCommonData.variables()["order_status_one_work_day"] in self.get_availability_status():
            return True
        return False

    def get_availability_status_digital_licence(self) -> bool:
        if (PlCommonData.variables()["order_status_digital"] in self.get_availability_status()
             and "BOX" not in self.get_product_name()):
            return True
        return False

    def get_lift_service_available_status(self) -> bool:
        return self.wait_for.element_in_elements_visible(self.locator.ELEMENT_product_lift_service_available,
                                                         timeout=self.TIMEOUT_SHORT, raise_exception=False)

    def get_temporarily_unavailable_status(self) -> bool:
        return self.wait_for.element_in_elements_visible(self.locator.ELEMENT_product_temporarily_unavailable,
                                                         timeout=self.TIMEOUT_SHORT, raise_exception=False)

    def get_unavailable_status(self) -> bool:
        return self.wait_for.element_in_elements_visible(self.locator.ELEMENT_product_unavailable,
                                                         timeout=self.TIMEOUT_SHORT, raise_exception=False)

    def check_alert(self) -> ProductPageAlertKey | None:
        if self.wait_for.element_visible(self.locator.ELEMENT_alert, raise_exception=False,
                                         timeout=self.TIMEOUT_MEDIUM):
            if self.wait_for.element_visible(self.locator.ELMENT_limited_sale_alert,
                                             raise_exception=False, timeout=self.TIMEOUT_SHORT):
                return ProductPageAlertKey.LIMITED_SALE_EXCEEDED
            else:
                return ProductPageAlertKey.GENERAL_ALERT
        return None

    def get_limited_sale_status(self) -> dict | None:
        def __parse_stock_info(text: str):
            nums = list(map(int, re.findall(r'\d+', text)))
            ls_left = nums[0]
            total = nums[1]
            ls_sold = total - ls_left
            return ls_left, ls_sold

        ls = self.wait_for.element_in_elements_visible(self.locator.ELEMENT_product_limited_sale_available,
                                                       timeout=self.TIMEOUT_SHORT, raise_exception=False)
        if ls:
            if self.wait_for.element_visible(self.locator.ELEMENT_product_limited_sale_status,
                                             raise_exception=False, timeout=self.TIMEOUT_SHORT) is None:
                return {"limited_sale_left": None, "limited_sale_sold": None}
            else:
                ls_status = self.wait_for.element_in_elements_visible(
                    self.locator.ELEMENT_product_limited_sale_status).text
                ls_left, ls_sold = __parse_stock_info(ls_status)
                return {"limited_sale_left": ls_left, "limited_sale_sold": ls_sold}
        return None

    def get_outlet_status(self) -> bool:
        return PlCommonData.variables()["outlet_offer"] in self.wait_for.element_visible(
            self.locator.ELEMENT_product_name).text

    def action_click_add_to_cart(self):
        self.wait_for.element_visible(self.get_add_to_cart_button())
        self.click_element(self.get_add_to_cart_button())

    def get_min_qty_for_order(self) -> int | None:
        if self.wait_for.element_visible(self.locator.ELEMENT_min_qty):
            return int(self.wait_for.element_visible(self.locator.ELEMENT_min_qty).get_attribute("data-min-qty"))
        return None

    def get_crossed_out_price(self) -> dict:
        def __get_float_price(price_element: CommonPO.WebElementCommon | None) -> float | None:
            if price_element:
                regex = r'-?\s*\d+(?:\s*\d+)*[.,]?\d*'
                match = re.search(regex, price_element.text)
                return float(match.group().replace(" ", "").replace(",", "."))
            return None

        base_price_element = self.wait_for.element_visible(ProductPageLocators.ELEMENT_base_price,
                                                           timeout=self.TIMEOUT_SHORT, raise_exception=False)
        final_price_element = self.wait_for.element_visible(ProductPageLocators.ELEMENT_final_price,
                                                            timeout=self.TIMEOUT_SHORT, raise_exception=False)
        price_badge_element = self.wait_for.element_visible(ProductPageLocators.ELEMENT_price_badge,
                                                            timeout=self.TIMEOUT_SHORT, raise_exception=False)
        omnibus_price = self.wait_for.element_visible(ProductPageLocators.ELEMENT_omnibus_price,
                                                      timeout=self.TIMEOUT_SHORT, raise_exception=False)

        base_price_element = __get_float_price(base_price_element)
        final_price_element = __get_float_price(final_price_element)
        price_badge_element = __get_float_price(price_badge_element)
        omnibus_price = __get_float_price(omnibus_price)

        if self.wait_for.element_visible(ProductPageLocators.ELEMENT_outlet_price,
                                                      timeout=self.TIMEOUT_SHORT, raise_exception=False):
            outlet_price = __get_float_price(self.wait_for.element_visible(ProductPageLocators.ELEMENT_outlet_price,
                                                      timeout=self.TIMEOUT_SHORT, raise_exception=False))
            return {
                "base_price": base_price_element,
                "final_price": final_price_element,
                "price_badge": price_badge_element,
                "omnibus_price": omnibus_price,
                "outlet_price": outlet_price
            }
        else:
            return {
                "base_price": base_price_element,
                "final_price": final_price_element,
                "price_badge": price_badge_element,
                "omnibus_price": omnibus_price,
            }

    @staticmethod
    def assert_product_data_from_url_data(product_data: dict, assertion: str, reference_url: str) -> bool:
        def url_processor() -> str:
            data_from_url = reference_url.split("/")[-1].split(".")[0]
            if "-" in data_from_url:
                data_from_url = data_from_url.split("-")[0]
            if "," in data_from_url:
                data_from_url = data_from_url.split(",")[0]
            return data_from_url

        data = [element.lower() for element in product_data[assertion]]
        url_data = url_processor()

        match assertion:
            case "maker":
                if url_data in maker_exceptions.keys():
                    url_data = maker_exceptions[url_data]
            case "breadcrumbs":
                if url_data in breadcrumbs_exceptions.keys():
                    url_data = breadcrumbs_exceptions[url_data]

        for element in data:
            if url_data in element:
                return True
        return False

    def get_product_data(self, products_urls: CommonPO.ListCommon[str], random_elements: int = 3) -> \
            CommonPO.ListCommon[dict]:
        def get_breadcrumbs() -> CommonPO.ListCommon[str]:
            self.wait_for.element_visible(ProductPageLocators.ELEMENT_product_breadcrumbs)
            return self.driver.locator(ProductPageLocators.ELEMENT_product_breadcrumbs).all_inner_texts()

        def get_random_products_urls() -> CommonPO.ListCommon[str]:
            if random_elements >= len(products_urls):
                return products_urls
            else:
                return random.sample(products_urls, random_elements)

        products_urls = get_random_products_urls()
        products = []
        self.time.sleep(self.TIMEOUT_MEDIUM)
        for product in products_urls:
            self.driver.get(product)
            self.time.sleep(self.TIMEOUT_SHORT)
            product_name = self.wait_for.element_visible(ProductPageLocators.ELEMENT_product_name,
                                                         raise_exception=False, timeout=self.TIMEOUT_LONG)
            if product_name:
                pass
            else:
                self.driver.refresh()
            LayerWithProductRecommendationPageObjects(self.driver).skip_recommendation_layer_if_visible()
            maker_element = self.wait_for.element_visible(
                ProductPageLocators.ELEMENT_product_maker,
                timeout=self.TIMEOUT_MEDIUM,
                raise_exception=False,
            )
            products.append({
                "url": product,
                "maker": [maker_element.text] if maker_element else [],
                "breadcrumbs": get_breadcrumbs()
            })
        return products

    def add_product_to_wishlist(self):
        self.wait_for.element_visible(ProductPageLocators.BUTTON_add_to_wishlist).click()


class ProductLabelsPageObjects(ProductPageObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def get_label_within_price_container(self, label_alt: str) -> bool:
        return self.wait_for.element_visible(self.locator.ELEMENT_product_label_within_main_box.format(label_alt),
                                             raise_exception=False)

    def get_label_description_within_description_container(self, label_alt: str) -> bool:
        return self.wait_for.element_visible(
            self.locator.ELEMENT_product_label_within_product_description.format(label_alt), raise_exception=False)

    def get_label_url_within_description_container(self, label_url: str) -> bool:
        return self.wait_for.element_visible(
            self.locator.ELEMENT_product_label_within_product_description_url.format(label_url), raise_exception=False)


class ProductOpinionPageObjects(ProductPageObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def add_consumer_review(self, review: str):
        self.scroll_to.element(self.wait_for.element_visible(ProductOpinionPageLocators.CONTAINER_add_review))
        self.send_keys(self.wait_for.element_visible(ProductOpinionPageLocators.INPUT_add_review), review)
        self.wait_for.element_visible(ProductOpinionPageLocators.BUTTON_add_review).click()

    def get_customer_reviews(self) -> [str]:
        self.scroll_to.element(self.wait_for.element_visible(ProductOpinionPageLocators.CONTAINER_reviews))
        self.wait_for.element_visible(ProductOpinionPageLocators.CONTAINER_reviews_list)
        while self.wait_for.element_visible(ProductOpinionPageLocators.BUTTON_extend_hidden_customer_reviews,
                                            raise_exception=False):
            self.wait_for.element_visible(
                ProductOpinionPageLocators.BUTTON_extend_hidden_customer_reviews).click()
        return self.driver.locator(ProductOpinionPageLocators.ELEMENTS_customer_review).all_inner_texts()


class ProductPromotionsPageObjects(ProductPageObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def get_promotion_visibility(self, promotion_title: str) -> bool:
        return self.wait_for.element_visible(
            ProductPageLocators.ELEMENT_promotion.format(promotion_title=promotion_title), raise_exception=False)


class ProductPromoCodePageObjects(ProductPageObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def get_promo_code_data(self) -> dict | False:
        if self.wait_for.element_visible(ProductPagePriceContainerLocators.ELEMENT_promo_code_label,
                                         raise_exception=False, timeout=self.TIMEOUT_SHORT):
            promo_code_value = self.wait_for.element_visible(
                ProductPagePriceContainerLocators.ELEMENT_promo_code_value).text
            promo_code_price = self.wait_for.element_visible(
                ProductPagePriceContainerLocators.ELEMENT_promo_code_price).text
            return {
                "promo_code": promo_code_value,
                "promo_code_price": promo_code_price,
            }
        return False
