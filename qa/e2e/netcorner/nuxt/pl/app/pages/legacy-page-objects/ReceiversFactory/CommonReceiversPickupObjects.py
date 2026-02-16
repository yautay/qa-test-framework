from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CheckoutLocators,
    MyAccountReceiversManagerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.LayersLocators import (
    NewReceiverStorehouseLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiverObjectsModel import (
    ReceiversObjectsModel,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import ComponentContextKey


class CommonReceiversPickupObjects(ReceiversObjectsModel):
    def __init__(self, driver, test_data: dict):
        super().__init__(driver)
        self.test_data = test_data
        self.test_data["checkout_data"] = []
        self.delivery_object_data = None

    def _set_checkout_data(self, element: str):
        if element not in self.test_data["checkout_data"] and element != "":
            self.test_data["checkout_data"].append(element)

    def _get_existing_receivers_objects(self) -> ReceiversObjectsModel.ListCommon[ReceiversObjectsModel.WebElementCommon]:
        if self.test_data["component_context"] == ComponentContextKey.CHECKOUT:
            locator = self.driver.locator(
                CheckoutLocators.CONTAINER_receiver_objects_parcell + CheckoutLocators.ELEMENTS_receiver_tiles
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
                    return True
        return False

    def _scroll_receiver_objects(self, iterations: int, iteration: int) -> None:
        scroll_container = self.wait_for.element_visible(
            NewReceiverStorehouseLayerLocators.ELEMENT_receiver_objects_scroll,
            timeout=self.TIMEOUT_SHORT,
            raise_exception=False,
        )
        if scroll_container:
            scroll_container.locator.evaluate(
                "(el, args) => { el.scrollTop = (el.scrollHeight / args.iterations) * args.iteration; }",
                {"iterations": iterations, "iteration": iteration},
            )

    def assert_data(self, test_data: dict):
        self.delivery_object_data = test_data["delivery_object"]
        if "delivery_location" not in self.delivery_object_data or "delivery_point_name" not in self.delivery_object_data:
            raise AttributeError("Missing required test data")

    def _click_zoom_out_if_enabled(self) -> bool:
        zoom_out_button = self.wait_for.element_visible(
            NewReceiverStorehouseLayerLocators.BUTTON_zoom_out_map,
            raise_exception=False,
            timeout=1,
        )
        if not zoom_out_button:
            return False
        if (zoom_out_button.get_attribute("aria-disabled") or "").lower() == "true":
            return False
        if zoom_out_button.get_attribute("disabled") is not None:
            return False
        if not zoom_out_button.is_enabled():
            return False
        zoom_out_button.click()
        return True

    def select_object(self, delivery_point_name: str):
        def __iterate_to_get_object():
            iterations = 10
            iteration = 1
            while iteration <= iterations:
                self._scroll_receiver_objects(iterations, iteration)
                rcvr_object = self.wait_for.element_visible(
                    NewReceiverStorehouseLayerLocators.ELEMENT_receiver_objects_tile_by_name.format(
                        object_name=delivery_point_name), raise_exception=False)
                if rcvr_object:
                    self.click_element(rcvr_object)
                    return True
                iteration += 1
            return False

        while self.wait_for.element_visible(NewReceiverStorehouseLayerLocators.ELEMENT_zoom_in_request,
                                            timeout=1, raise_exception=False):
            self.wait_for.element_visible(NewReceiverStorehouseLayerLocators.BUTTON_zoom_in_map).click()
        if not __iterate_to_get_object():
            self._click_zoom_out_if_enabled()
            if not __iterate_to_get_object():
                raise Exception(f"Receiver object {delivery_point_name} not found")

    def get_objects(self):
        self.test_data["checkout_data"].clear()
        iterations = 10
        iteration = 1
        previous_count = 0
        stagnant_iterations = 0
        self._click_zoom_out_if_enabled()
        while self.wait_for.element_visible(NewReceiverStorehouseLayerLocators.ELEMENT_zoom_in_request,
                                            timeout=1, raise_exception=False):
            self.wait_for.element_visible(NewReceiverStorehouseLayerLocators.BUTTON_zoom_in_map).click()
        while iteration <= iterations:
            self._scroll_receiver_objects(iterations, iteration)
            self.time.sleep(0.1)
            storehouses = self.driver.locator(NewReceiverStorehouseLayerLocators.ELEMENTS_receiver_objects_available)
            for storehouse_idx in range(storehouses.count()):
                self._set_checkout_data(storehouses.nth(storehouse_idx).inner_text())

            current_count = len(self.test_data["checkout_data"])
            if current_count == previous_count:
                stagnant_iterations += 1
                if stagnant_iterations >= 2:
                    break
            else:
                stagnant_iterations = 0
            previous_count = current_count
            iteration += 1

    def fill_new_receiver_object(self):
        pass

    def edit_existing_receiver_object(self):
        pass

    def assert_existing_receiver_objects(self) -> bool:
        pass

    def delete_existing_receiver_object(self):
        pass

    def back_to_checkout(self):
        self.wait_for.element_visible(NewReceiverStorehouseLayerLocators.BUTTON_close_layer).click()

    def enter_form_layer(self, skip_if_receiver_exists: bool = True) -> bool:
        if skip_if_receiver_exists:
            if self._check_existing_objects_and_select():
                return False
        if self.test_data["component_context"] == ComponentContextKey.CHECKOUT:
            self.wait_for.element_visible(
                CheckoutLocators.CONTAINER_receiver_objects_parcell + CheckoutLocators.BUTTON_add_receiver_tile).click()
        elif self.test_data["component_context"] == ComponentContextKey.ACCOUNT:
            self.wait_for.element_visible(MyAccountReceiversManagerLocators.BUTTON_add_receiver_tile).click()
        return True
