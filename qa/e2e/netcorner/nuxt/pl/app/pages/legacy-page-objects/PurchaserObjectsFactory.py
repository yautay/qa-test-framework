from abc import ABC, abstractmethod

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CheckoutLocators,
    MyAccountPurchasersManagerLocators,
    NewPrivatePurchaserLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.LayersLocators import (
    CommonPurchaserLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects import PurchaserLayerObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.LayersObjects import (
    CommonPurchaserReceiverLayerObject,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import ComponentContextKey, PurchaserKey


class PurchaserObjectFactory(CommonPO):
    def __init__(self, driver, test_data: dict, component_context: ComponentContextKey):
        """
        :param test_data: test's test_data dictionary
        :type test_data: dict
        :param component_context: Interface context
        :type component_context: enum
        """
        super().__init__(driver)
        self.data_object = []
        self.test_data = test_data
        self._component_context = component_context
        self._object_name: str
        self._set_object_name()

    def _set_object_name(self):
        match self.test_data["purchaser_object"]["order_as"]:
            case PurchaserKey.PRIVATE:
                self._method_class = PurchaserPrivateObjects(self.driver, self.test_data)
                pur_data_type = self.test_data['purchaser_object'].get('purchaser_data')
                if isinstance(pur_data_type, dict):
                    self._object_name = (f"{pur_data_type.get('name', '')} "
                                         f"{pur_data_type.get('surname', '')}")
                else:
                    self._object_name = str(pur_data_type)
            case PurchaserKey.COMPANY:
                self._method_class = PurchaserCompanyObjects(self.driver, self.test_data)
                self._object_name = self.test_data["purchaser_object"]["purchaser_data"]["company"]

    def _get_locators_class(self) -> MyAccountPurchasersManagerLocators | CheckoutLocators:
        match self._component_context:
            case ComponentContextKey.CHECKOUT:
                return CheckoutLocators()
            case ComponentContextKey.ACCOUNT:
                return MyAccountPurchasersManagerLocators()

    def _get_existing_purchaser_objects(self) -> CommonPO.ListCommon[CommonPO.WebElementCommon] or None:
        if self._component_context == ComponentContextKey.CHECKOUT:
            if self.wait_for.element_visible(CheckoutLocators.CONTAINER_purchaser_objects, raise_exception=False):
                locator = self.driver.locator(CheckoutLocators.ELEMENTS_purchaser_tiles)
                return [locator.nth(idx) for idx in range(locator.count())]
        elif self._component_context == ComponentContextKey.ACCOUNT:
            locator = self.driver.locator(MyAccountPurchasersManagerLocators.ELEMENTS_purchaser_tiles)
            return [locator.nth(idx) for idx in range(locator.count())]
        return None

    def close_layer(self):
        self.wait_for.element_visible(NewPrivatePurchaserLayerLocators.BUTTON_close_layer).click()

    def add_new_purchaser_object(self, skip_if_purchaser_exists: bool = True):
        """
        Adds new purchaser Object corresponding to test_data type of purchaser object provided.
        :param skip_if_purchaser_exists: select existing purchaser if exists
        :type skip_if_purchaser_exists: bool
        """
        existing_purchasers = self._get_existing_purchaser_objects()
        if existing_purchasers and skip_if_purchaser_exists:
            for element in existing_purchasers:
                if element.is_visible():
                    element.click()
                    return True
        else:
            match self._component_context:
                case ComponentContextKey.CHECKOUT:
                    self.click_element(self.wait_for.element_visible(CheckoutLocators.BUTTON_add_purchaser_tile))
                case ComponentContextKey.ACCOUNT:
                    self.wait_for.element_visible(
                        MyAccountPurchasersManagerLocators.BUTTON_add_purchaser_tile).click()
            self._method_class.fill_new_purchaser_object()

    def edit_existing_purchaser_object(self):
        if self._component_context == ComponentContextKey.CHECKOUT:
            tile_dropdown = self.wait_for.element_visible(MyAccountPurchasersManagerLocators.CONTAINER_purchaser +
                MyAccountPurchasersManagerLocators.BUTTON_edit_purchaser_tile_by_name_dropdown.format(
                    name=self._object_name), timeout=self.TIMEOUT_LONG)
            self.click_element(tile_dropdown)
            tile_edit = self.wait_for.element_visible(MyAccountPurchasersManagerLocators.CONTAINER_purchaser +
                MyAccountPurchasersManagerLocators.BUTTON_edit_purchaser_tile_by_name.format(
                    name=self._object_name), timeout=self.TIMEOUT_LONG)
            self.click_element(tile_edit)
        elif self._component_context == ComponentContextKey.ACCOUNT:
            tile_dropdown = self.wait_for.element_visible(
                MyAccountPurchasersManagerLocators.BUTTON_edit_purchaser_tile_by_name_dropdown.format(
                    name=self._object_name))
            self.click_element(tile_dropdown)
            tile_edit = self.wait_for.element_visible(
                MyAccountPurchasersManagerLocators.BUTTON_edit_purchaser_tile_by_name.format(
                    name=self._object_name))
            self.click_element(tile_edit)
        self.test_data["purchaser_object"] = self.test_data["purchaser_object_edited"]
        self._method_class.fill_new_purchaser_object()
        self._set_object_name()

    def delete_existing_purchaser_object(self):
        dropdown_locator = MyAccountPurchasersManagerLocators.BUTTON_edit_purchaser_tile_by_name_dropdown.format(
            name=self._object_name
        )
        remove_dropdown = self.wait_for.element_visible(
            dropdown_locator)
        self.click_element(remove_dropdown)
        remove_confirm = self.wait_for.element_visible(
            MyAccountPurchasersManagerLocators.BUTTON_delete_purchaser_tile_by_name.format(
                name=self._object_name))
        self.click_element(remove_confirm)
        self.wait_for.element_visible(NewPrivatePurchaserLayerLocators.BUTTON_confirm_delete_purchaser).click()
        self.wait_for.element_invisible(dropdown_locator, timeout=self.TIMEOUT_LONG)
        assert not self.wait_for.element_visible(dropdown_locator, raise_exception=False, timeout=self.TIMEOUT_SHORT)

    def assert_existing_purchaser_objects(self):
        def _get_purchaser_objects() -> list[list[str]]:
            purchasers_list = []
            locators_class = self._get_locators_class()
            purchaser_locator = self.driver.locator(locators_class.ELEMENTS_purchaser_tiles)
            for purchaser_idx in range(purchaser_locator.count()):
                element = purchaser_locator.nth(purchaser_idx)
                data = []
                data_cells = element.locator(f"xpath={locators_class.ELEMENTS_tiles_data}")
                for cell_idx in range(data_cells.count()):
                    data.append(data_cells.nth(cell_idx).inner_text())
                purchasers_list.append(data)
            return purchasers_list

        purchasers_objects = _get_purchaser_objects()
        for purchaser in purchasers_objects:
            if self._object_name in purchaser:
                return True
        return False

    def fill_and_validate_form_errors(self):
        if not self.element_visibility.get_element_visibility(NewPrivatePurchaserLayerLocators.CONTAINER_add_purchaser_layer):
            self.add_new_purchaser_object()
        else:
            self._method_class.fill_new_purchaser_object()
        self._method_class.compare_errors_in_new_purchaser_form()


class PurchaserObjectsModel(ABC, CommonPO):
    @abstractmethod
    def fill_new_purchaser_object(self):
        pass


class PurchaserCompanyObjects(PurchaserObjectsModel):
    def __init__(self, driver, test_data: dict):
        super().__init__(driver)
        self.test_data = test_data

    def fill_new_purchaser_object(self):
        PurchaserLayerObject(self.driver).fill_new_company_purchaser_object(self.test_data)

    def compare_errors_in_new_purchaser_form(self):
        CommonPurchaserReceiverLayerObject(self.driver).compare_errors_new_purchaser_receiver_form(self.test_data, "purchaser")


class PurchaserPrivateObjects(PurchaserObjectsModel):
    def __init__(self, driver, test_data: dict):
        super().__init__(driver)
        self.test_data = test_data

    def fill_new_purchaser_object(self):
        if self.element_visibility.get_element_visibility(NewPrivatePurchaserLayerLocators.CHECKBOX_copy_data_checked):
            self.wait_for.element_visible(NewPrivatePurchaserLayerLocators.CHECKBOX_copy_data_checked).click()
            self.wait_for.element_visible(NewPrivatePurchaserLayerLocators.CHECKBOX_copy_data_unchecked)
            self.wait_for.element_visible(CommonPurchaserLayerLocators.BUTTON_company_purchaser).click()
            self.wait_for.element_visible(CommonPurchaserLayerLocators.BUTTON_private_purchaser).click()

        PurchaserLayerObject(self.driver).fill_new_private_purchaser_object(self.test_data)

    def compare_errors_in_new_purchaser_form(self):
        CommonPurchaserReceiverLayerObject(self.driver).compare_errors_new_purchaser_receiver_form(self.test_data, "purchaser")
