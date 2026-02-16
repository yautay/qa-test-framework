import random
import re

from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CheckoutLocators,
    MyAccountReceiversManagerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.LayersLocators import (
    CommonReceiverLayerLocators,
    NewReceiverCourierLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects import ReceiverLayerObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.LayersObjects import (
    CommonPurchaserReceiverLayerObject,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiverObjectsModel import (
    ReceiversObjectsModel as ROM,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    ComponentContextKey,
    DeliveryMatrixKey,
    ReceiverKey,
)


class ReceiversCourierObjects(ROM):
    """
        This class represents Delivery with courier methods of receiver objects.
        It provides methods for filling a new receiver object and retrieving the available objects.

        :param driver: WebDriver object
        :param test_data: dict object with provided test data nested under "delivery_object" key :
            - "receiver_data" - - MANDATORY key with PlCommonData dict type receiver data values
            - "order_with" - MANDATORY key with DeliveryMethodKey value
            - "receiver_type": MANDATORY key with ReceiverKey value
            - "matrix_tile_price_limit": - OPTIONAL key with DeliveryMatrixKey value for selecting desired delivery method tile.
            - "matrix": - OPTIONAL key with bool valle for assertion of desired delivery method provider (matrix vs. list)
        :return: None
    """

    def __init__(self, driver, test_data: dict):
        super().__init__(driver)
        self.test_data = test_data
        self._object_name: str
        self._set_object_name()

    def _set_object_name(self):
        if "receiver_data" not in self.test_data["delivery_object"]:
            raise AttributeError("Missing required test_data[\"receiver_data\"]")
        else:
            name = self.test_data["delivery_object"]["receiver_data"]["name"]
            surname = self.test_data["delivery_object"]["receiver_data"]["surname"]
            company = self.test_data["delivery_object"]["receiver_data"]["company"]
            match self.test_data["delivery_object"]["receiver_type"]:
                case ReceiverKey.PRIVATE:
                    self._object_name = f"{name} {surname}"
                case ReceiverKey.COMPANY:
                    self._object_name = f"{company}"

    def _assert_data(self):
        if "receiver_type" not in self.test_data["delivery_object"]:
            raise AttributeError("Missing required test_data[\"receiver_type\"]")
        if "receiver_data" not in self.test_data["delivery_object"] or not all(
                key in self.test_data["delivery_object"]["receiver_data"] for key in
                ["name", "surname", "street_name", "street_number",
                 "postal_code",
                 "city", "phone", "mail"]):
            raise AttributeError("Missing required test_data[\"receiver_data\"]")

    def _fill_receiver_form(self):
        ReceiverLayerObject(self.driver).fill_receiver_form(self.test_data)

    def _get_delivery_matrix(self) -> ROM.WebElementCommon:
        return self.wait_for.element_visible(
            NewReceiverCourierLayerLocators.CONTAINER_delivery_matrix, timeout=self.TIMEOUT_SHORT, raise_exception=False)

    def _get_delivery_matrix_tiles(self) -> ROM.ListCommon[ROM.WebElementCommon]:
        self.wait_for.element_visible(NewReceiverCourierLayerLocators.ELEMENT_delivery_matrix_item)
        tiles_locator = self.driver.locator(NewReceiverCourierLayerLocators.ELEMENT_delivery_matrix_item)
        tiles = [tiles_locator.nth(idx) for idx in range(tiles_locator.count())]
        tiles_final = []
        for tile in tiles:
            if len(tile.inner_text()) > 0:
                tiles_final.append(tile)
        return tiles_final

    def _get_delivery_list(self) -> ROM.WebElementCommon:
        return self.wait_for.element_visible(
            NewReceiverCourierLayerLocators.CONTAINER_delivery_list, timeout=self.TIMEOUT_SHORT, raise_exception=False)

    def _get_delivery_list_items(self) -> ROM.ListCommon[ROM.WebElementCommon]:
        items_locator = self.driver.locator(NewReceiverCourierLayerLocators.ELEMENT_delivery_list_item)
        return [items_locator.nth(idx) for idx in range(items_locator.count())]

    def _get_existing_receivers_objects(self) -> ROM.ListCommon[ROM.WebElementCommon]:
        if self.test_data["component_context"] == ComponentContextKey.CHECKOUT:
            locator = self.driver.locator(
                CheckoutLocators.CONTAINER_receiver_objects_courier + CheckoutLocators.ELEMENTS_receiver_tiles
            )
            return [locator.nth(idx) for idx in range(locator.count())]
        elif self.test_data["component_context"] == ComponentContextKey.ACCOUNT:
            locator = self.driver.locator(MyAccountReceiversManagerLocators.ELEMENTS_receiver_tiles)
            return [locator.nth(idx) for idx in range(locator.count())]
        return []

    def _check_existing_objects_and_select(self) -> bool:
        existing_receivers = self._get_existing_receivers_objects()
        if len(existing_receivers) > 0:
            for element in existing_receivers:
                if element.is_visible():
                    element.click()
                    self._select_courier_method()
                    return True
        return False

    def _select_courier_method(self):
        """
            Method responsible for selection delivery option either form matrix or list of available methods.
            Parameters are obtained form test_data dictionary provided in class constrictor.
            Important OPTIONAL items form test_data for this method are:
            test_data["delivery_object"]["matrix_tile_price_limit"]: str - represents string value of price corresponding with desired method.
            If provided, method will select only tiles with provided price value.
            test_data["delivery_object"]["matrix"]: bool - represent desired type of delivery options, matrix or list.
            If provided, method will ASSERT visibility of desired type of method provider.
            """
        def _get_filtered_matrix_tiles(tiles: ROM.ListCommon[ROM.WebElementCommon]) -> ROM.ListCommon[ROM.WebElementCommon]:
            filtered_tiles = []
            price_limit: DeliveryMatrixKey | False = False
            if "matrix_tile_price_limit" in self.test_data["delivery_object"].keys():
                price_limit = self.test_data["delivery_object"]["matrix_tile_price_limit"]
            if price_limit:
                for tile in tiles:
                    if price_limit.value == tile.inner_text():
                        filtered_tiles.append(tile)
            else:
                return tiles
            return filtered_tiles

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        delivery_matrix = self._get_delivery_matrix()
        delivery_list = self._get_delivery_list()

        if "matrix" in self.test_data["delivery_object"].keys():
            match self.test_data["delivery_object"]["matrix"]:
                case True:
                    assert not delivery_list
                    assert delivery_matrix
                    random.choice(_get_filtered_matrix_tiles(self._get_delivery_matrix_tiles())).click()
                case False:
                    assert not delivery_matrix
                    assert delivery_list
                    random.choice(self._get_delivery_list_items()).click()
        else:
            if delivery_matrix:
                random.choice(_get_filtered_matrix_tiles(self._get_delivery_matrix_tiles())).click()
            elif self._get_delivery_list_items():
                random.choice(self._get_delivery_list_items()).click()

    def get_available_objects(self):
        pass

    def back_to_checkout(self):
        self.wait_for.element_visible(NewReceiverCourierLayerLocators.BUTTON_close_layer).click()

    def enter_form_layer(self, skip_if_receiver_exists: bool = True) -> bool:
        if skip_if_receiver_exists:
            if self._check_existing_objects_and_select():
                return False
        if self.test_data["component_context"] == ComponentContextKey.CHECKOUT:
            order_picker = CheckoutLocators.CONTAINER_receiver_objects_courier + CheckoutLocators.BUTTON_add_receiver_tile
            if not self.wait_for.element_visible(order_picker, raise_exception=False):
                if self.wait_for.element_visible(CheckoutLocators.BOX_warning_message, raise_exception=False):
                    self.driver.refresh()
                    self.click_element(self.wait_for.element_visible(order_picker))
            else:
                self.wait_for.element_visible(
                    CheckoutLocators.CONTAINER_receiver_objects_courier + CheckoutLocators.BUTTON_add_receiver_tile).click()
        elif self.test_data["component_context"] == ComponentContextKey.ACCOUNT:
            self.wait_for.element_visible(MyAccountReceiversManagerLocators.BUTTON_add_receiver_tile).click()
        return True

    def fill_new_receiver_object(self):
        self._assert_data()
        self._fill_receiver_form()
        self._select_courier_method()

    def fill_account_receiver_object(self, test_data):
        self._fill_receiver_form()

    def compare_errors_in_new_receiver_form(self, test_data):
        CommonPurchaserReceiverLayerObject(self.driver).compare_errors_new_purchaser_receiver_form(test_data, "receiver")

    def edit_existing_receiver_object(self):
        self.wait_for.element_visible(
            MyAccountReceiversManagerLocators.BUTTON_edit_receiver_tile_by_name_dropdown.format(
                name=self._object_name)).click()
        self.wait_for.element_visible(
            MyAccountReceiversManagerLocators.BUTTON_edit_receiver_tile_by_name.format(
                name=self._object_name)).click()
        self.test_data["delivery_object"] = self.test_data["delivery_object_edited"]
        self.fill_new_receiver_object()
        self._set_object_name()

    def assert_existing_receiver_objects(self) -> bool:
        match self.test_data["component_context"]:
            case ComponentContextKey.ACCOUNT:
                locators_class = MyAccountReceiversManagerLocators
            case ComponentContextKey.CHECKOUT:
                locators_class = CheckoutLocators

        def _get_receiver_objects() -> list[list[str]]:
            receivers_list = []
            receivers_locator = self.driver.locator(locators_class.ELEMENTS_receiver_tiles)
            for receiver_idx in range(receivers_locator.count()):
                element = receivers_locator.nth(receiver_idx)
                data = []
                data_cells = element.locator(f"xpath={locators_class.ELEMENTS_tiles_data}")
                for cell_idx in range(data_cells.count()):
                    data.append(data_cells.nth(cell_idx).inner_text())
                receivers_list.append(data)
            return receivers_list

        def _remove_special_characters_and_spaces(input_str) -> str:
            cleaned_str = re.sub(r'[^A-Za-z0-9]', '', input_str)
            return cleaned_str

        self.wait_for.element_visible(locators_class.ELEMENTS_receiver_tiles)
        receivers_objects = _get_receiver_objects()
        for receiver in receivers_objects:
            for receiver_data in receiver:
                if _remove_special_characters_and_spaces(self._object_name) in _remove_special_characters_and_spaces(
                        receiver_data):
                    return True
        return False

    def delete_existing_receiver_object(self):
        dropdown_locator = MyAccountReceiversManagerLocators.BUTTON_edit_receiver_tile_by_name_dropdown.format(
            name=self._object_name
        )
        self.wait_for.element_visible(
            dropdown_locator).click()
        self.wait_for.element_visible(
            MyAccountReceiversManagerLocators.BUTTON_delete_receiver_tile_by_name.format(
                name=self._object_name)).click()
        self.wait_for.element_visible(CommonReceiverLayerLocators.BUTTON_confirm_delete_receiver).click()
        self.wait_for.element_invisible(dropdown_locator, timeout=self.TIMEOUT_LONG)
        assert not self.wait_for.element_visible(dropdown_locator, raise_exception=False, timeout=self.TIMEOUT_SHORT)

    def select_courier_method(self):
        self._select_courier_method()
