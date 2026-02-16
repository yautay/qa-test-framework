import re

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CartLayerLocators,
    CartLocators,
    CartOfferLocators,
    CartProductContainerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.HeaderObjects import (
    HeaderObjects,
)
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import AlertKey, ToastKey


class CartObjects(CommonPO):
    def __init__(self, driver, *args):
        super().__init__(driver)

    def is_limited_sale_visible_in_cart(self) -> bool:
        return self.wait_for.element_visible(CartProductContainerLocators.ELEMENT_limited_sale_banner,
                                             raise_exception=False)

    def click_move_further(self) -> [AlertKey] or None:
        button_move = self.wait_for.element_visible(CartLocators.BUTTON_move_further, timeout=self.TIMEOUT_MEDIUM)
        self.click_element(button_move)
        alerts = self.get_cart_alerts()
        if alerts:
            if AlertKey.ALERT_CART_PRICE_CHANGED in alerts:
                self.wait_for.element_visible(CartLocators.BUTTON_move_further).click()
        return alerts

    def get_cart_alerts(self) -> CommonPO.ListCommon[AlertKey] or None:
        common_alerts = PlCommonData.alerts()
        visible_alerts = []
        for k, v in common_alerts.items():
            if self.wait_for.element_visible(
                    CartLocators.ELEMENT_alert.format(alert_msg=v), timeout=self.TIMEOUT_SHORT, raise_exception=False):
                visible_alerts.append(AlertKey(k))
        return visible_alerts or None

    def get_move_further_button_activity(self) -> bool:
        end_time = self.time.time() + self.TIMEOUT_SHORT
        last_state = None
        stable_reads = 0

        while self.time.time() <= end_time:
            button = self.wait_for.element_visible(CartLocators.BUTTON_move_further, raise_exception=False)
            if not button:
                return False

            classes = button.get_attribute("class") or ""
            aria_disabled = (button.get_attribute("aria-disabled") or "").lower() == "true"
            has_disabled_attr = button.get_attribute("disabled") is not None
            has_enabled_class = CartLocators.BUTTON_move_further_enabled in classes

            current_state = bool(button.is_enabled() and not aria_disabled and not has_disabled_attr and has_enabled_class)

            if current_state == last_state:
                stable_reads += 1
            else:
                last_state = current_state
                stable_reads = 1

            if stable_reads >= 2:
                return current_state

            self.time.sleep(0.2)

        return bool(last_state)

    def get_cart_value(self) -> dict:
        self.wait_for.element_visible(CartLocators.CONTAINER_per_product)

        def __get_elements_text(row_locator, child_xpath: str) -> CommonPO.ListCommon[str]:
            if child_xpath.startswith("//"):
                child_xpath = f".{child_xpath}"
            return row_locator.locator(f"xpath={child_xpath}").all_inner_texts()

        def __get_elements_attr(row_locator, child_xpath: str, attr_name: str) -> CommonPO.ListCommon[str]:
            if child_xpath.startswith("//"):
                child_xpath = f".{child_xpath}"
            elements = row_locator.locator(f"xpath={child_xpath}")
            values = []
            for element_idx in range(elements.count()):
                value = elements.nth(element_idx).get_attribute(attr_name)
                if value is not None:
                    values.append(value)
            return values

        def __get_price_from_elements(elements_list: CommonPO.ListCommon[str]) \
                -> float | CommonPO.ListCommon[float] | None:
            if len(elements_list) > 0:
                prices = []
                for element in elements_list:
                    regex = r'-?\s*\d+[.,]?\d*'
                    price_match = re.search(regex, element)
                    if not price_match:
                        continue
                    price_value = float(price_match.group().replace(" ", "").replace(",", "."))
                    prices.append(price_value)
                if len(prices) == 0:
                    return None
                if len(prices) == 1:
                    return prices[0]
                else:
                    return prices
            else:
                return None

        def __get_qty_from_elements(elements_list: CommonPO.ListCommon[str]) -> int | CommonPO.ListCommon[int] | None:
            if len(elements_list) > 0:
                qty = []
                for element in elements_list:
                    qty_value = int(element)
                    qty.append(qty_value)
                if len(qty) == 1:
                    return qty[0]
                else:
                    return qty
            else:
                return None

        products = {}
        product_rows = self.driver.locator(CartLocators.CONTAINER_per_product)
        for product_idx in range(product_rows.count()):
            product = product_rows.nth(product_idx)
            product_id_attr = product.get_attribute("data-product-id")
            if not product_id_attr:
                continue
            product_id = int(product_id_attr)
            price_base_element = __get_price_from_elements(
                __get_elements_text(product, CartProductContainerLocators.ELEMENT_price_base))
            price_final_element = __get_price_from_elements(
                __get_elements_text(product, CartProductContainerLocators.ELEMENTS_price_gross))
            price_omnibus = __get_price_from_elements(
                __get_elements_text(product, CartProductContainerLocators.ELEMENT_price_omnibus))
            product_qty = __get_qty_from_elements(
                __get_elements_attr(product, CartProductContainerLocators.ELEMENT_qty, "value"))

            products.update({product_id: {
                "price_base": price_base_element,
                "price_final": price_final_element,
                "price_omnibus": price_omnibus,
                "qty": product_qty,
            }})
        raw_price = self.wait_for.element_visible(CartLocators.ELEMENT_cart_value).text
        normalized_price = raw_price.replace(" ", "").replace("\xa0", "").replace("zł", "").replace(",", ".")
        float_price = float(normalized_price)
        return {
            "products": products,
            "raw_price": raw_price,
            "float_price": float_price
        }

    def __get_cart_products(self):
        self.wait_for.element_visible(CartLocators.ELEMENT_cart_step_selector)

    def get_cart_products_ids(self) -> [int]:
        self.wait_for.element_visible(CartLocators.ELEMENT_cart_step_selector)
        products_ids = []
        product_containers = self.driver.locator(CartLocators.CONTAINER_per_product)
        for idx in range(product_containers.count()):
            product_id = product_containers.nth(idx).get_attribute("data-product-id")
            if product_id:
                products_ids.append(int(product_id))
        return products_ids

    def empty_cart(self):
        empty_cart_btn = self.wait_for.element_visible(CartLocators.BUTTON_empty_cart,
                                                               timeout=self.TIMEOUT_SHORT, raise_exception=False)
        if empty_cart_btn:
            self.scroll_to.element(empty_cart_btn, additional_scroll=1500, sleep_time=self.TIMEOUT_SHORT)
            empty_cart_btn.click()
            self.wait_for.element_visible(CartLayerLocators.BUTTON_clean_cart_confirm).click()

    def get_cart_products_names(self):
        return self.wait_for.element_visible(CartLocators.ELEMENT_product_name).accessible_name


class CartCleaner(CommonPO):
    def __init__(self, driver):
        super().__init__(driver)

    def clean_cart(self):
        HeaderObjects(self.driver, None).go_to_cart()
        self.time.sleep(self.TIMEOUT_MEDIUM)
        CartObjects(self.driver).empty_cart()
        HeaderObjects(self.driver, None).go_to_homepage()


class CartProductPriceObjects(CartObjects):
    def __init__(self, driver, *args):
        super().__init__(driver, *args)


class CartProductAmountObjects(CartObjects):
    def __init__(self, driver, *args):
        super().__init__(driver, *args)

    def action_adjust_product_quantity_by_product_id(self, product_id: int, required_product_amount: int,
                                                     assert_final_amount: bool = False) -> ToastKey | None:
        def cart_quantity() -> int:
            return int(self.wait_for.element_visible(
                CartLocators.INPUT_product_quantity.format(product_id=product_id)).get_attribute("value"))

        def get_toast(toast_txt: str) -> ToastKey:
            common_toasts = PlCommonData.toasts()
            for k, v in common_toasts.items():
                if v in toast_txt:
                    return ToastKey(k)

        while cart_quantity() != required_product_amount:
            cart_qty = cart_quantity()
            if required_product_amount > cart_quantity():
                if self.wait_for.element_visible(
                        CartLocators.BUTTON_product_quantity_increase.format(product_id=product_id),
                        raise_exception=False, timeout=self.TIMEOUT_SHORT):
                    increase_btn = self.wait_for.element_visible(
                        CartLocators.BUTTON_product_quantity_increase.format(product_id=product_id),
                        raise_exception=False, timeout=self.TIMEOUT_SHORT)
                    if increase_btn:
                        increase_btn.click()
                    else:
                        return None
                toast = self.wait_for.element_visible(CartLocators.TOAST_cart, timeout=self.TIMEOUT_NUXT_TOASTS,
                                                      raise_exception=False)
                if toast:
                    assert cart_qty == cart_quantity()
                    return get_toast(toast.text)
            elif required_product_amount < cart_quantity():
                if self.wait_for.element_visible(
                        CartLocators.BUTTON_product_quantity_decrease.format(product_id=product_id),
                        raise_exception=False, timeout=self.TIMEOUT_SHORT):
                    decrease_btn = self.wait_for.element_visible(
                        CartLocators.BUTTON_product_quantity_decrease.format(product_id=product_id),
                        raise_exception=False, timeout=self.TIMEOUT_SHORT)
                    if decrease_btn:
                        decrease_btn.click()
                    else:
                        return None
                toast = self.wait_for.element_visible(CartLocators.TOAST_cart, timeout=self.TIMEOUT_NUXT_TOASTS,
                                                      raise_exception=False)
                if toast:
                    assert cart_qty == cart_quantity()
                    return get_toast(toast.text)
        if assert_final_amount:
            assert int(self.wait_for.element_visible(
                CartLocators.INPUT_product_quantity.format(product_id=product_id)).get_attribute(
                "value")) == required_product_amount
        return None


class CartPromoCodeObject(CartObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def add_promo_code(self, promo_code: str) -> bool:
        self.send_keys(self.wait_for.element_visible(CartLocators.INPUT_promo_code), promo_code)
        self.click_element(self.wait_for.element_visible(CartLocators.BUTTON_add_promo_code))
        return self.wait_for.element_visible(CartLocators.ELEMENT_added_code.format(code=promo_code),
                                             raise_exception=False)


class CartOfferObjects(CartObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def is_offer_available(self) -> bool:
        return self.wait_for.element_visible(CartOfferLocators.BUTTON_add_offer_to_cart,
                                             raise_exception=False) is not None

    def add_offer_to_cart(self) -> bool:
        button = self.wait_for.element_visible(CartOfferLocators.BUTTON_add_offer_to_cart, raise_exception=False)
        if button and button.is_enabled():
            button.click()
            return True
        return False

    def get_cart_offer_value(self) -> float:
        return float(
            self.wait_for.element_visible(CartOfferLocators.ELEMENT_offer_price).text.strip().replace(" ", "").replace(
                "zł", "").replace(",", "."))
