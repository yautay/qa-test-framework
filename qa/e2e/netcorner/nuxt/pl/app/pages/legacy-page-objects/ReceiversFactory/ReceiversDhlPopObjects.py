from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.LayersLocators import (
    NewReceiverDhlPopLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.CommonReceiversPickupObjects import (
    CommonReceiversPickupObjects,
)


class ReceiversDhlPopObjects(CommonReceiversPickupObjects):
    """
    CheckoutReceiversDhlPopObjects encapsulates DHLPOP delivery method tile objects
    """

    def __init__(self, driver, test_data: dict):
        super().__init__(driver, test_data)

    def _get_available_objects(self, location: str):
        self.send_keys(self.wait_for.element_visible(NewReceiverDhlPopLayerLocators.INPUT_postal_code_searchbar),
                       location, clear=True)
        self.wait_for.element_visible(NewReceiverDhlPopLayerLocators.BUTTON_search).click()
        self.get_objects()

    def back_to_checkout(self):
        self.wait_for.element_visible(NewReceiverDhlPopLayerLocators.BUTTON_close_layer).click()

    def fill_new_receiver_object(self):
        """
        Fills new receiver tile with delivery data
        and gets available objects from list to class variable.

        :param test_data: test's test_data object with keys "delivery_location" and "delivery_point_name
        :type test_data: dict
        """
        self.assert_data(self.test_data)
        self.wait_for.element_visible(NewReceiverDhlPopLayerLocators.CONTAINER)
        self._get_available_objects(self.delivery_object_data["delivery_location"])
        self.select_object(self.delivery_object_data["delivery_point_name"])
        self.wait_for.element_visible(NewReceiverDhlPopLayerLocators.BUTTON_close_layer).click()
