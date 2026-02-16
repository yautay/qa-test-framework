from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib import PageObjects as Page
from TestData.pl_komputronik_nuxt.PlCommonKeys import ButtonNameKey

from ..PageLocators import ConfiguratorLocators, ProductListLocators
from ..PageObjects import MontageLayerObject


class ConfiguratorObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

        self.locator = ConfiguratorLocators()
        self.locator_shop = ProductListLocators()

    @property
    def section_mandatory_elements(self):
        element = self.wait_for.element_visible(self.locator.SECTION_mandatory_elements)
        return element

    def wait_for_selected_item(self, item_name: str):
        self.wait_for_spinner_disappear()
        self.wait_for.element_visible(self.locator.LIST_selected_set_items)
        if not self.wait_for.element_visible(self.locator.ELEMENT_selected_set_items.format(item_name),
                                             raise_exception=False):
            raise AssertionError(f"Selected item '{item_name}' is not visible in the selected items list.")


class SelectItemFromConfiguratorSetList(ConfiguratorObjects):
    def __init__(self, driver, item_name: str):
        super().__init__(driver)

        self.mandatory_element = self.locator.LIST_mandatory_elements.format(item_name)
        self.optional_element = self.locator.LIST_optional_elements.format(item_name)

    def select_mandatory_components(self):
        self.scroll_to.top()
        self.wait_for.element_visible(self.section_mandatory_elements)
        self.wait_for.element_visible(self.mandatory_element).click()
        self.wait_for.element_visible(self.locator_shop.MAIN_CONTAINER_product_list)

    def select_optional_components(self):
        self.scroll_to.top()
        if not self.wait_for.element_visible(self.locator.BUTTON_section_optional_expanded, raise_exception=False):
            self.wait_for.element_visible(self.locator.BUTTON_expand_section_optional).click()
        self.wait_for.element_visible(self.locator.SECTION_optional_elements)
        self.wait_for.element_visible(self.optional_element).click()
        self.wait_for.element_visible(self.locator_shop.MAIN_CONTAINER_product_list)

    def click_select_mandatory_components(self):
        self.driver.refresh()
        self.time.sleep(self.TIMEOUT_NUXT_TOASTS)
        self.select_mandatory_components()

    def click_select_optional_components(self):
        self.driver.refresh()
        self.time.sleep(self.TIMEOUT_NUXT_TOASTS)
        self.select_optional_components()


class AssemblyNewSetFromConfigurator(ConfiguratorObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def choose_and_assembly_components(self, components, element_order):
        for item in components:
            if element_order == "mandatory":
                Page.SelectItemFromConfiguratorSetList(self.driver, item).click_select_mandatory_components()
            elif element_order == "optional":
                Page.SelectItemFromConfiguratorSetList(self.driver, item).click_select_optional_components()
            Page.ProductListObject(self.driver).select_product_from_listing()
            Page.LayerPromotionsObject(self.driver).close_layer_if_visible()
            Page.SelectItemFromConfiguratorSetList(self.driver, item).wait_for_selected_item(item)


class GoToConfiguratorSummary(ConfiguratorObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def assert_configurator_summary(self):
        summary_button = self.locator.BUTTON_go_to_summary
        self.scroll_to.element(summary_button)
        self.wait_for.element_visible(summary_button).click()
        return self.wait_for.element_visible(self.locator.CONTAINER_summary).is_displayed()

    def assert_error_section(self, is_section_visible: bool):
        if is_section_visible:
            self.wait_for.element_visible(self.locator.SECTION_error)
            error_text = self.driver.locator(self.locator.ERROR_text).first.inner_text()
            assert error_text == "Obecna konfiguracja zawiera błędy"

    def assert_order_buttons_activity(self, button_name: ButtonNameKey):
        if button_name == ButtonNameKey.BOTH:
            self.wait_for.element_visible(self.locator.BUTTON_order_as_set)
            self.wait_for.element_visible(self.locator.BUTTON_order_as_parts)
            return True
        elif button_name == ButtonNameKey.PARTS:
            return self.wait_for.element_visible(self.locator.BUTTON_order_as_parts).is_displayed()
        elif button_name == ButtonNameKey.SET:
            return self.wait_for.element_visible(self.locator.BUTTON_order_as_set).is_displayed()

    def click_button_order_as(self, button_name: ButtonNameKey, pc_montage: bool):
        if pc_montage:
            self.scroll_to.element(self.locator.CONTAINER_footer)

        button_loc = self.locator.BUTTON_order_as_parts if button_name == ButtonNameKey.PARTS \
            else self.locator.BUTTON_order_as_set
        self.scroll_to.element(button_loc)
        self.wait_for.element_visible(button_loc).click()

        MontageLayerObject(self.driver).apply_montage_changes(pc_montage) if button_name == ButtonNameKey.SET else ...

    def check_visibility_of_elements(self, test_data):
        elements = [
            self.assert_configurator_summary(),
            self.assert_error_section(test_data["error_section_visible"]),
            self.assert_order_buttons_activity(test_data["active_buttons"])
        ]
        return elements
