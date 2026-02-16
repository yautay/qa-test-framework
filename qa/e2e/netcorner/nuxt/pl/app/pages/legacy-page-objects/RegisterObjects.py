from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import RegisterPageLocators


class RegisterObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

        self.locator = RegisterPageLocators()

    def verify_visibility_of_register_form_elements(self) -> bool | str:
        register_form_elements = self.locator.ELEMENTS_register_form_combined
        for key, value in register_form_elements.items():
            if not self.wait_for.element_visible(value, raise_exception=False):
                return key
        return False

    def register_new_customer(self, test_data: dict) -> bool:
        if self.wait_for.element_visible(RegisterPageLocators.CONTAINER_register_page):
            assert "register_data" in test_data.keys()
            self.send_keys(RegisterPageLocators.INPUT_login, test_data["register_data"]["email"])
            self.send_keys(RegisterPageLocators.INPUT_password, test_data["register_data"]["password"])
            self.send_keys(RegisterPageLocators.INPUT_password_repeated, test_data["register_data"]["password"])
            self.wait_for.element_visible(RegisterPageLocators.CHECKBOX_customer_company_rules_terms).click()
            self.resolve_re_captcha()
            self.wait_for.element_visible(RegisterPageLocators.BUTTON_register_user).click()
            login_in_use = self.wait_for.element_visible(
                RegisterPageLocators.TOAST_negative, raise_exception=False, timeout=self.TIMEOUT_NUXT_TOASTS)
            if login_in_use:
                return False
            else:
                return True
        else:
            raise Exception("Register Form not visible")

    def resolve_re_captcha(self):
        self.wait_for.element_visible(RegisterPageLocators.IFRAME_re_captcha)
        self.scroll_to.element(RegisterPageLocators.IFRAME_re_captcha, additional_scroll=-500)
        recaptcha_frame = self.driver.page.frame_locator(RegisterPageLocators.IFRAME_re_captcha.replace("//", "xpath=//", 1))
        recaptcha_checkbox = recaptcha_frame.locator(RegisterPageLocators.CHECKBOX_re_captcha.replace("//", "xpath=//", 1)).first
        recaptcha_checked = recaptcha_frame.locator(RegisterPageLocators.re_captcha_checked.replace("//", "xpath=//", 1)).first

        if not recaptcha_checked.is_visible(timeout=self.TIMEOUT_SHORT * 1000):
            recaptcha_checkbox.wait_for(state="visible", timeout=self.TIMEOUT_TEST * 1000)
            recaptcha_checkbox.click()

        self.time.sleep(self.TIMEOUT_SHORT)

    def check_if_captcha_checked(self):
        recaptcha_frame = self.driver.page.frame_locator(RegisterPageLocators.IFRAME_re_captcha.replace("//", "xpath=//", 1))
        recaptcha_checked = recaptcha_frame.locator(RegisterPageLocators.re_captcha_checked.replace("//", "xpath=//", 1)).first
        recaptcha_checked.wait_for(state="visible", timeout=self.TIMEOUT_TEST * 1000)

    def compare_errors_register_form(self, test_data: dict):
        error_messages = test_data["register_data_errors"]
        error_messages_in_form = {}
        for key, value in RegisterPageLocators.forms_error_messages().items():
            if self.element_visibility.get_element_visibility(value):
                error_messages_in_form[key] = self.wait_for.element_visible(value).text

        for key in error_messages_in_form:
            if key not in ["phone_code"]:
                actual = error_messages_in_form[key]
                expected = error_messages[key]
                assert actual == expected, f"Actual error {actual} is not equal to expected error {expected}"
