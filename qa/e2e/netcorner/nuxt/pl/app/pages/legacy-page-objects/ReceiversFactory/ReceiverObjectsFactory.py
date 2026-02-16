from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CheckoutLocators,
    CommonReceiverLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversCourierObjects import (
    ReceiversCourierObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversDhlPopObjects import (
    ReceiversDhlPopObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversDigitalObjects import (
    ReceiversDigitalObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversInpostObjects import (
    ReceiversInpostObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversLiftObjects import (
    ReceiversLiftObjects,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversStorehouseObjects import (
    ReceiversStorehouseObjects,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import ComponentContextKey, DeliveryMethodKey


class ReceiversObjectsFactory(CommonBasePageObject):
    """
    Initialize the CheckoutReceiversObjectsInterface class.

    :param driver: the Selenium WebDriver instance
    :type driver: WebDriver
    :param test_data: test's test_data dictionary
    :type test_data: dict
    """

    def __init__(self, driver, test_data: dict, component_context: ComponentContextKey):
        super().__init__(driver)
        self.test_data = test_data
        self.test_data["component_context"] = component_context

        if "delivery_object" not in test_data.keys():
            raise AttributeError("Missing required test_data[\"delivery_object\"] key")
        if "order_with" not in test_data["delivery_object"].keys():
            raise AttributeError("Missing required test_data[\"order_with\"] key")
        self._delivery_method = test_data["delivery_object"]["order_with"]

        match self._delivery_method:
            case DeliveryMethodKey.COURIER:
                self._method_class = ReceiversCourierObjects(driver, self.test_data)
            case DeliveryMethodKey.COURIER_WITH_LIFT | DeliveryMethodKey.COURIER_WITHOUT_LIFT:
                self._method_class = ReceiversLiftObjects(driver, self.test_data)
            case DeliveryMethodKey.STOREHOUSE:
                self._method_class = ReceiversStorehouseObjects(driver, self.test_data)
            case DeliveryMethodKey.INPOST:
                self._method_class = ReceiversInpostObjects(driver, self.test_data)
            case DeliveryMethodKey.DHLPOP:
                self._method_class = ReceiversDhlPopObjects(driver, self.test_data)
            case DeliveryMethodKey.DIGITAL:
                self._method_class = ReceiversDigitalObjects(driver, self.test_data)

    def back_to_checkout(self):
        """
        Brings the user back to the checkout page.

        :return: None
        """
        self._method_class.back_to_checkout()

    def add_new_receiver_object(self, skip_if_receiver_exists: bool = True):
        if self._method_class.enter_form_layer(skip_if_receiver_exists=skip_if_receiver_exists):
            self._method_class.fill_new_receiver_object()

    def edit_existing_receiver_object(self):
        self._method_class.edit_existing_receiver_object()

    def receiver_object_assertions(self, assertions: CommonBasePageObject.ListCommon[dict]):
        """
        Asserts the visibility of receiver objects based on the provided assertions.

        :param assertions: A list of dictionaries containing the following keys:
            - delivery_location: The delivery location to check for available objects.
            - object_visibility: A boolean indicating whether the object should be visible or not.
            - delivery_point_name: The name of the delivery point to assert.
        :return: None
        """
        self.wait_for.element_visible(CheckoutLocators.BUTTON_add_receiver_tile).click()
        for assertion_dict in assertions:
            self._method_class.get_available_objects(assertion_dict["delivery_location"])
            if assertion_dict["object_visibility"]:
                assert assertion_dict["delivery_point_name"] in self.test_data["checkout_data"]
                print("asserted {} visible".format(assertion_dict["delivery_point_name"]))
            else:
                assert assertion_dict["delivery_point_name"] not in self.test_data["checkout_data"]
                print("asserted {} not visible".format(assertion_dict["delivery_point_name"]))
        self.back_to_checkout()

    def delete_existing_receiver_object(self):
        self._method_class.delete_existing_receiver_object()

    def assert_existing_receiver_objects(self):
        assert self._method_class.assert_existing_receiver_objects()

    def fill_and_validate_form_errors(self):
        if not self.element_visibility.get_element_visibility(CommonReceiverLayerLocators.CONTAINER_add_receiver_layer):
            self.add_new_receiver_object()
        else:
            self._method_class.fill_account_receiver_object(self.test_data)
        self._method_class.compare_errors_in_new_receiver_form(self.test_data)

    def select_delivery_time_and_method(self):
        self._method_class.select_courier_method()
