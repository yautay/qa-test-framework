import re

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CheckoutLocators,
    NewPrivatePurchaserLayerLocators,
    OrderDetailsThankYouPageLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.PurchaserObjectsFactory import (
    PurchaserObjectFactory,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiverObjectsFactory import (
    ReceiversObjectsFactory,
)
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    AlertKey,
    ComponentContextKey,
    DeliveryMethodKey,
)


class CheckoutObjects(CommonPO):
    """
    Initializes a new instance of the CheckoutObjects class.

    :param driver: The WebDriver object for interacting with the browser.
    :type driver: WebDriver
    """

    def __init__(self, driver):
        super().__init__(driver)

    def go_back_to_cart(self):
        """
        Navigates back to the cart page.

        :return: None
        """
        self.wait_for.element_visible(CheckoutLocators.BUTTON_back_to_cart).click()

    def add_comment_to_order(self, comment: str):
        """
        Add a comment to the order.

        :param comment: The comment to be added to the order
        :return: None
        """
        self.wait_for.element_visible(CheckoutLocators.CHECKBOX_add_comment).click()
        self.send_keys(self.wait_for.element_visible(CheckoutLocators.INPUT_comments), comment, sleep_time=self.TIMEOUT_SHORT)

    def accept_terms(self):
        """
        Clicks on the terms checkbox to accept the terms and conditions.

        :return: None
        """
        self.wait_for.element_visible(CheckoutLocators.CHECKBOX_terms).click()
        outlet = self.wait_for.element_visible(CheckoutLocators.CHECKBOX_terms_outlet, timeout=self.TIMEOUT_SHORT,
                                                       raise_exception=False)
        if outlet:
            outlet.click(self.TIMEOUT_SHORT)

    def accept_terms_digital(self):
        """
        Clicks on the terms checkbox to accept the terms and conditions concerning digital products.

        :return: None
        """
        element = self.wait_for.element_visible(CheckoutLocators.CHECKBOX_terms_digital, timeout=self.TIMEOUT_SHORT,
                                                        raise_exception=False)
        if element:
            element.click(self.TIMEOUT_SHORT)

    def accept_terms_mca_license(self):
        """
        Clicks on the terms checkbox to accept the terms and conditions concerning digital products on MCA license.

        :return: None
        """
        element = self.wait_for.element_visible(CheckoutLocators.CHECKBOX_mca_license_digital,
                                                        raise_exception=False)
        if element:
            element.click(self.TIMEOUT_MEDIUM)

    def submit_order(self) -> None:
        """
        Submits the order by clicking the submit order button.

        :return: None
        """
        self.wait_for.element_visible(CheckoutLocators.BUTTON_submit_order).click()
        self.wait_for.element_visible(OrderDetailsThankYouPageLocators.ELEMENT_order_number, timeout=self.TIMEOUT_LONG)

    def get_checkout_alerts(self) -> CommonPO.ListCommon[AlertKey] | None:
        """
        Returns a list of visible checkout alerts.

        :return: A list of AlertKey objects representing the visible checkout alerts, or None if there are no visible alerts.
        :rtype: list[AlertKey] | None
        """
        common_alerts = PlCommonData.alerts()
        visible_alerts = []
        for k, v in common_alerts.items():
            if self.wait_for.element_visible(
                    CheckoutLocators.ELEMENT_alert.format(alert_msg=v), timeout=self.TIMEOUT_SHORT, raise_exception=False):
                visible_alerts.append(AlertKey(k))
        return visible_alerts or None


class ChooseDeliveryMethodObjects(CommonPO):
    """
    ChooseDeliveryMethodObjects Class
    """

    def __init__(self, driver):
        super().__init__(driver)
        self.driver = driver
        self.delivery_method = None

    def select_delivery_method(self, test_data: dict):
        """
        Selects the delivery method based on the provided test data.

        :param test_data: A dictionary containing the test data.
                          The dictionary should have the following structure:
                          {
                              "delivery_object": {
                                  "order_with": <delivery method>,
                                  "methods_allowed": [<method 1>, <method 2>, ...]
                              }
                          }
                          - "order_with" (optional): The preferred delivery method to use.
                          - "methods_allowed" (optional): A list of delivery methods allowed.

        :return: None
        :raises Exception: If a delivery method is not allowed or not visible.
        """
        if "order_with" in test_data["delivery_object"].keys():
            self.delivery_method = test_data["delivery_object"]["order_with"]
        else:
            self.delivery_method = DeliveryMethodKey.STOREHOUSE

        available_delivery_methods = []
        if "methods_allowed" in test_data["delivery_object"].keys():
            available_delivery_methods = self.__get_delivery_methods_visibility()
        else:
            self.wait_for.element_visible(CheckoutLocators.CONTAINER_shipping_methods)
        self.__select_delivery_method(self.delivery_method)
        if "methods_allowed" in test_data["delivery_object"].keys():
            for method_available in available_delivery_methods:
                print(f"{method_available} checked in available")
                if method_available not in test_data["delivery_object"]["methods_allowed"]:
                    raise Exception(f"method {method_available.value} not allowed!")
            for method_allowed in test_data["delivery_object"]["methods_allowed"]:
                if method_allowed not in available_delivery_methods:
                    raise Exception(f"method {method_allowed.value} not visible!")
                print(f"{method_allowed} checked in allowed")

    def __get_delivery_methods_visibility(self) -> CommonPO.ListCommon[DeliveryMethodKey]:
        """
        Returns a list of delivery methods that are currently visible on the checkout page.

        :return: A list of DeliveryMethodKey enum values.
        """
        methods = []
        self.wait_for.element_visible(CheckoutLocators.CONTAINER_shipping_methods)

        if self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_delivery, timeout=1, raise_exception=False):
            methods.append(DeliveryMethodKey.COURIER)
        if self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_inpost, timeout=1, raise_exception=False):
            methods.append(DeliveryMethodKey.INPOST)
        if self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_dhlpop, timeout=1, raise_exception=False):
            methods.append(DeliveryMethodKey.DHLPOP)
        if self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_storehouse, timeout=1, raise_exception=False):
            methods.append(DeliveryMethodKey.STOREHOUSE)
        if self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_digital, timeout=1, raise_exception=False):
            methods.append(DeliveryMethodKey.DIGITAL)

        return methods

    def __select_delivery_method(self, delivery_method: DeliveryMethodKey):
        """
        Selects a delivery method based on the given DeliveryMethodKey.

        :param delivery_method: The DeliveryMethodKey representing the desired delivery method.
        :return: None
        """
        match delivery_method:
            case DeliveryMethodKey.STOREHOUSE:
                self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_storehouse).click(
                    self.TIMEOUT_NUXT_TOASTS)
            case DeliveryMethodKey.COURIER:
                self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_delivery).click(
                    self.TIMEOUT_NUXT_TOASTS)
            case DeliveryMethodKey.COURIER_WITH_LIFT | DeliveryMethodKey.COURIER_WITHOUT_LIFT:
                self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_delivery).click(
                    self.TIMEOUT_NUXT_TOASTS)
            case DeliveryMethodKey.INPOST:
                self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_inpost).click(
                    self.TIMEOUT_NUXT_TOASTS)
            case DeliveryMethodKey.DHLPOP:
                self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_dhlpop).click(
                    self.TIMEOUT_NUXT_TOASTS)
            case DeliveryMethodKey.DIGITAL:
                self.wait_for.element_visible(CheckoutLocators.BUTTON_checkout_digital).click(
                    self.TIMEOUT_NUXT_TOASTS)


class CheckoutReceiverObjectsFactory(ReceiversObjectsFactory):
    def __init__(self, driver, test_data: dict):
        super().__init__(driver, test_data, component_context=ComponentContextKey.CHECKOUT)


class CheckoutPurchaserObjectsFactory(PurchaserObjectFactory):
    def __init__(self, driver, test_data: dict):
        super().__init__(driver, test_data, component_context=ComponentContextKey.CHECKOUT)


class CheckoutPaymentObjects(CommonPO):
    def __init__(self, driver):
        super().__init__(driver)

    def select_payment(self, test_data):
        self.wait_for.element_invisible(NewPrivatePurchaserLayerLocators.CONTAINER_add_purchaser_layer)
        payment = PlCommonData.payments()[test_data["payment_option"]]
        self.wait_for.element_visible(CheckoutLocators.CONTAINER_payment)
        self.wait_for.element_visible(
            CheckoutLocators.ELEMENT_payment_tile_by_name.format(payment=payment)).click()


class CheckoutThankYouPage(CommonPO):
    def __init__(self, driver):
        super().__init__(driver)

    def get_typ_order_data(self) -> dict:
        def __get_float_price(string_price: str) -> float:
            regex = r'-?\s*\d{1,3}(?:[ \d]{0,3})*(?:[.,]?\d+)?'
            match = re.search(regex, string_price)
            return float(match.group().replace(" ", "").replace(",", "."))

        return {
            "order_number": self.wait_for.element_visible(OrderDetailsThankYouPageLocators.ELEMENT_order_number,
                                                          timeout=self.TIMEOUT_LONG).text,
            "shipping_price": __get_float_price(self.wait_for.element_visible(
                OrderDetailsThankYouPageLocators.ELEMENT_order_shipping_value, timeout=self.TIMEOUT_LONG).text),
            "summary_price": __get_float_price(
                self.wait_for.element_visible(OrderDetailsThankYouPageLocators.ELEMENT_order_value,
                                              timeout=self.TIMEOUT_LONG).text)
        }
