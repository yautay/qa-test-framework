from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    PasswordRecoveryPageLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.RegisterObjects import (
    RegisterObjects,
)


class PasswordRecoveryObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def add_new_password(self, test_data: dict):
        self.wait_for.element_visible(PasswordRecoveryPageLocators.INPUT_new_password).send_keys(
            test_data["register_data"]["password"])
        self.wait_for.element_visible(PasswordRecoveryPageLocators.INPUT_new_password_repeat).send_keys(
            test_data["register_data"]["password"])
        RegisterObjects(self.driver).resolve_re_captcha()
        self.wait_for.element_visible(PasswordRecoveryPageLocators.BUTTON_save_changes).click()
