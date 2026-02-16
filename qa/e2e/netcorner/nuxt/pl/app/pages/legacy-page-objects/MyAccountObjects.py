from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    ChangePasswordPageLocators,
    MyAccountLocators,
    MyAccountOrdersSummaryLocators,
    OrderDetailsPageLocators,
    WishlistPageLocators,
)


class MyAccountObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def enter_purchasers_manager(self):
        self.time.sleep(self.TIMEOUT_SHORT)
        self.wait_for.element_visible(MyAccountLocators.BUTTON_manage_purchasers).click()

    def enter_receivers_manager(self):
        self.time.sleep(self.TIMEOUT_SHORT)
        self.wait_for.element_visible(MyAccountLocators.BUTTON_manage_receivers).click()

    def enter_orders_summary(self):
        self.wait_for.element_visible(MyAccountLocators.BUTTON_orders_summary).click()

    def enter_wishlist_summary(self):
        self.wait_for.element_visible(MyAccountLocators.BUTTON_wishlist_summary).click()

    def get_account_logged_as(self) -> str:
        return self.wait_for.element_visible(MyAccountLocators.ELEMENT_account_login).text


class MyAccountOrderSummary(MyAccountObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def enter_order_summary(self, order_number: str):
        self.wait_for.element_visible(
            MyAccountOrdersSummaryLocators.BUTTON_order_by_number.format(order_number=order_number)).click()

    def get_order_summary_data(self) -> dict:
        self.time.sleep(self.TIMEOUT_SHORT)
        return {
            "order_status": self.wait_for.element_visible(MyAccountOrdersSummaryLocators.ELEMENT_order_status).text,
            "order_value": self.wait_for.element_visible(MyAccountOrdersSummaryLocators.ELEMENT_order_value).text
        }


class AccountChangePasswordObjects(MyAccountObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def fill_form(self, passwords_data):
        passwords_data = self.param_dict_has_expected_keys(passwords_data, ("new_password", "old_password"))
        self.send_keys(ChangePasswordPageLocators.INPUT_old_password, passwords_data["old_password"])
        self.send_keys(ChangePasswordPageLocators.INPUT_new_password, passwords_data["new_password"])
        self.send_keys(ChangePasswordPageLocators.INPUT_new_password_repeated, passwords_data["new_password"],
                       sleep_time=self.TIMEOUT_SHORT)

    def save_password_change(self):
        self.wait_for.element_visible(ChangePasswordPageLocators.BUTTON_save_changes).click(self.TIMEOUT_NUXT_TOASTS)


class OrderSummaryObjects(MyAccountObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def cancel_order(self):
        self.time.sleep(self.TIMEOUT_SHORT)
        self.wait_for.element_visible(OrderDetailsPageLocators.BUTTON_order_cancel).click()

    def have_negative_toast_appeared(self) -> CommonBasePageObject.WebElementCommon | None:
        return self.wait_for.element_visible(OrderDetailsPageLocators.TOAST_order_cancel_not_successful_alert,
                                             raise_exception=False, timeout=self.TIMEOUT_NUXT_TOASTS)

    def get_order_status(self):
        return self.wait_for.element_visible(OrderDetailsPageLocators.ELEMENT_order_status).text


class WishlistObjects(MyAccountObjects):
    def __init__(self, driver):
        super().__init__(driver)

    def go_on_product_page(self):
        self.wait_for.element_visible(WishlistPageLocators.LINK_product_href).click()

    def create_new_wishlist(self):
        self.wait_for.element_visible(WishlistPageLocators.BUTTON_create_wishlist).click()

    def delete_wishlist(self, list_name: str):
        self.wait_for.element_visible(WishlistPageLocators.BUTTON_delete_wishlist_by_name.format(name=list_name)).click()

    def check_if_delete_button_is_available(self, list_name: str) -> bool | CommonBasePageObject.WebElementCommon:
        self.time.sleep(self.TIMEOUT_SHORT)
        return self.wait_for.element_visible(WishlistPageLocators.BUTTON_delete_wishlist_by_name.format(name=list_name),
                                             raise_exception=False)

    def get_share_link(self, list_name: str):
        return self.wait_for.element_visible(WishlistPageLocators.BUTTON_share_wishlist.format(name=list_name))

    def add_product_to_cart(self):
        box = self.wait_for.element_visible(WishlistPageLocators.ELEMENT_product_box)
        self.time.sleep(self.TIMEOUT_SHORT)
        box.hover()
        self.wait_for.element_visible(WishlistPageLocators.BUTTON_add_product_to_cart).click()

    def delete_product_from_wishlist(self, product_id: str):
        self.wait_for.element_visible(WishlistPageLocators.BUTTON_delete_product.format(id=product_id)).click()

    def check_if_product_deletion_toast_appears(self):
        if self.wait_for.element_visible(WishlistPageLocators.TOAST_deleted_product):
            return True
