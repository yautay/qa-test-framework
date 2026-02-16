import random

from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.LayersLocators import (
    NewReceiverCourierLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversCourierObjects import (
    ReceiversCourierObjects,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import DeliveryMethodKey


class ReceiversLiftObjects(ReceiversCourierObjects):
    def __init__(self, driver, test_data: dict):
        super().__init__(driver, test_data)

    def _select_courier_method_with_lift(self):
        assert self.wait_for.element_visible(NewReceiverCourierLayerLocators.CHECKBOX_lift_service)
        if self.test_data["delivery_object"]["order_with"] == DeliveryMethodKey.COURIER_WITH_LIFT:
            lift_checkbox = self.wait_for.element_visible(NewReceiverCourierLayerLocators.CHECKBOX_lift_service, raise_exception=False)
            lift_checkbox.click() if lift_checkbox else ...
            assert self._get_delivery_list()
            assert not self._get_delivery_matrix()
            self.wait_for.element_visible(NewReceiverCourierLayerLocators.ELEMENT_delivery_with_lift).click()
        elif self.test_data["delivery_object"]["order_with"] == DeliveryMethodKey.COURIER_WITHOUT_LIFT:
            if self._get_delivery_matrix():
                random.choice(self._get_delivery_matrix_tiles()).click()
            elif self._get_delivery_list():
                random.choice(self._get_delivery_list_items()).click()
            else:
                raise Exception("Delivery methods not visible!")

    def fill_new_receiver_object(self):
        """
        Fills new tile with courier delivery data with lift

        :param test_data: test's test_data object with key "receiver_data"
        :type test_data: dict
        """
        self._assert_data()
        self._fill_receiver_form()
        self._select_courier_method_with_lift()
