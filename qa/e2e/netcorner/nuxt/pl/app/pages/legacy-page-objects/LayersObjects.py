from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators import (
    CookieLayerLocators,
    LayerWithPromotionsLocators,
    LoginLayerLocators,
    NewCompanyPurchaserLayerLocators,
    NewPrivatePurchaserLayerLocators,
    OpinionLayerLocators,
    SummaryCartLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.LayersLocators import (
    CommonPurchaserReceiverErrorsLayerLocators,
    LayerProductsAddedToCompareLocators,
    LayerWithProductRecommendation,
    LayerWithStorehouseAvailabilityLocators,
    MontageLayerLocators,
    NewReceiverCourierLayerLocators,
    ProductNewsletterLayerLocators,
    SalesManagoLayerLocators,
    WishlistLayerLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.RegisterObjects import (
    RegisterObjects,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import PurchaserKey, ReceiverKey

import settings


class CookieLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def close_cookie_layer(self):
        cookie_layer = self.wait_for.element_visible(
            CookieLayerLocators.CONTAINER_cookie_layer,
            raise_exception=False,
            timeout=self.TIMEOUT_LONG,
        )
        if cookie_layer:
            self.click_element(self.wait_for.element_visible(CookieLayerLocators.BUTTON_close_cookie_layer))
        if settings.server_type == "prod":
            sales_manago_frame = self.wait_for.element_visible(
                SalesManagoLayerLocators.CONTAINER_sales_manago_garbage,
                raise_exception=False,
            )
            if sales_manago_frame:
                self.driver.switch_to.frame(
                    sales_manago_frame)
                self.click_element(
                    self.wait_for.element_visible(SalesManagoLayerLocators.BUTTON_close_garbage_layer))
                self.driver.switch_to.default_content()


class LoginLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def login_layer_visibility(self) -> bool:
        return self.wait_for.element_visible(LoginLayerLocators.ELEMENT_login_layer_header, timeout=self.TIMEOUT_MEDIUM,
                                             raise_exception=False) or self.wait_for.element_visible(
            LoginLayerLocators.INPUT_login, raise_exception=False, timeout=self.TIMEOUT_MEDIUM)

    def login_user(self, credentials: dict, changed_password: bool = False):
        if self.login_layer_visibility() or changed_password:
            self.__send_credentials(credentials)
            self.__click_login_button()

    def enter_register_form(self):
        if self.login_layer_visibility():
            self.click_element(self.wait_for.element_visible(LoginLayerLocators.BUTTON_register))
        else:
            raise Exception("Login Layer not visible")

    def click_order_without_registration(self):
        self.wait_for.element_visible(LoginLayerLocators.BUTTON_order_without_registration).click()

    def click_and_recover_password(self, test_data: dict):
        self.wait_for.element_visible(LoginLayerLocators.BUTTON_reset_password).click()
        self.wait_for.element_visible(LoginLayerLocators.INPUT_reset_password_email).send_keys(test_data["register_data"]["email"])
        RegisterObjects(self.driver).resolve_re_captcha()
        self.wait_for.element_visible(LoginLayerLocators.BUTTON_send_password_reset).click()

    def __send_credentials(self, credentials: dict):
        self.send_keys(
            self.wait_for.element_visible(LoginLayerLocators.INPUT_login), credentials["email"],
        )
        self.send_keys(
            self.wait_for.element_visible(LoginLayerLocators.INPUT_password), credentials["password"],
        )

    def __click_login_button(self):
        self.wait_for.element_visible(LoginLayerLocators.BUTTON_login).click(self.TIMEOUT_NUXT_TOASTS)


class PurchaserLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def fill_new_company_purchaser_object(self, test_data: dict):
        purchaser_data = test_data["purchaser_object"]["purchaser_data"]

        def __without_gus_logic():
            self.wait_for.element_visible(NewCompanyPurchaserLayerLocators.CONTAINER_add_purchaser_layer)
            self.wait_for.element_visible(NewCompanyPurchaserLayerLocators.BUTTON_company_purchaser).click()
            if "country" in purchaser_data.keys():
                self.wait_for.element_visible(NewCompanyPurchaserLayerLocators.DROPDOWN_extend_country).click()
                self.wait_for.element_visible(
                    NewCompanyPurchaserLayerLocators.SELECT_country.format(country=purchaser_data["country"])).click()
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_nip, purchaser_data["nip"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_company, purchaser_data["company"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_street, purchaser_data["street_name"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_street_number, purchaser_data["street_number"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_postal_code, purchaser_data["postal_code"])
            if "country" in purchaser_data.keys():
                if "Polska" in purchaser_data["country"] or purchaser_data["country"] == "":
                    self.wait_for.element_visible(
                        NewCompanyPurchaserLayerLocators.DROPDOWN_extend_cities).click()
                    self.wait_for.element_visible(
                        NewCompanyPurchaserLayerLocators.SELECT_city.format(city_name=purchaser_data["city"]))
                else:
                    self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_city, purchaser_data["city"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_phone, purchaser_data["phone"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_email, purchaser_data["mail"])

        def __with_gus_logic():
            purchaser_data = test_data["purchaser_object"]["purchaser_data"]
            self.wait_for.element_visible(NewCompanyPurchaserLayerLocators.CONTAINER_add_purchaser_layer)
            self.wait_for.element_visible(NewCompanyPurchaserLayerLocators.BUTTON_company_purchaser).click()
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_nip, purchaser_data["nip_gus"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_phone, purchaser_data["phone"])
            self.send_keys(NewCompanyPurchaserLayerLocators.INPUT_email, purchaser_data["mail"])

        def __check_if_success():
            self.time.sleep(self.TIMEOUT_MEDIUM)
            if self.wait_for.element_visible(NewCompanyPurchaserLayerLocators.BUTTON_add_purchaser,
                                             raise_exception=False):
                return False
            return True

        def __complete_and_save_object():
            add_btn = self.wait_for.element_visible(
                NewCompanyPurchaserLayerLocators.BUTTON_add_purchaser, raise_exception=False)
            update_btn = self.wait_for.element_visible(
                NewCompanyPurchaserLayerLocators.BUTTON_update_purchaser, raise_exception=False)
            if add_btn:
                add_btn.click()
            elif update_btn:
                update_btn.click()

        if "nip_gus" in purchaser_data.keys():
            __with_gus_logic()
        else:
            __without_gus_logic()
        __complete_and_save_object()

        if not __check_if_success() and "nip_gus" in purchaser_data.keys():
            purchaser_data["nip"] = purchaser_data["nip_gus"]
            __without_gus_logic()
            __complete_and_save_object()

    def fill_new_private_purchaser_object(self, test_data: dict):
        purchaser_data = test_data["purchaser_object"]["purchaser_data"]
        self.wait_for.element_visible(NewPrivatePurchaserLayerLocators.CONTAINER_add_purchaser_layer)
        self.wait_for.element_visible(NewPrivatePurchaserLayerLocators.BUTTON_private_purchaser).click()
        self.send_keys(NewPrivatePurchaserLayerLocators.INPUT_name, purchaser_data["name"])
        self.send_keys(NewPrivatePurchaserLayerLocators.INPUT_surname, purchaser_data["surname"])
        self.send_keys(NewPrivatePurchaserLayerLocators.INPUT_street, purchaser_data["street_name"])
        self.send_keys(NewPrivatePurchaserLayerLocators.INPUT_street_number, purchaser_data["street_number"])
        self.send_keys(NewPrivatePurchaserLayerLocators.INPUT_postal_code, purchaser_data["postal_code"],
                       unfocus_input_after=True)
        self.wait_for.element_visible(NewPrivatePurchaserLayerLocators.DROPDOWN_extend_cities).click()
        city_empty = self.wait_for.element_visible(
            NewPrivatePurchaserLayerLocators.SELECT_city_empty,
            raise_exception=False,
        )
        if city_empty:
            city_empty.click()
        else:
            city = self.wait_for.element_visible(
                NewPrivatePurchaserLayerLocators.SELECT_city.format(city_name=purchaser_data["city"]),
                raise_exception=False,
            )
            if city:
                city.click()
        self.send_keys(NewPrivatePurchaserLayerLocators.INPUT_phone, purchaser_data["phone"])
        self.send_keys(NewPrivatePurchaserLayerLocators.INPUT_email, purchaser_data["mail"])
        add_btn = self.wait_for.element_visible(
            NewPrivatePurchaserLayerLocators.BUTTON_add_purchaser, raise_exception=False)
        update_btn = self.wait_for.element_visible(
            NewPrivatePurchaserLayerLocators.BUTTON_update_purchaser, raise_exception=False)
        if add_btn:
            add_btn.click()
        elif update_btn:
            update_btn.click()


class ReceiverLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def fill_receiver_form(self, test_data: dict):
        receiver_data = test_data["delivery_object"]["receiver_data"]
        if test_data["delivery_object"]["receiver_type"] == ReceiverKey.PRIVATE:
            self.wait_for.element_visible(NewReceiverCourierLayerLocators.BUTTON_private_receiver).click()
        else:
            self.wait_for.element_visible(NewReceiverCourierLayerLocators.BUTTON_company_receiver).click()
            self.send_keys(NewReceiverCourierLayerLocators.INPUT_company, receiver_data["company"])
        self.send_keys(NewReceiverCourierLayerLocators.INPUT_name, receiver_data["name"])
        self.send_keys(NewReceiverCourierLayerLocators.INPUT_surname, receiver_data["surname"])
        self.send_keys(NewReceiverCourierLayerLocators.INPUT_street, receiver_data["street_name"])
        self.send_keys(NewReceiverCourierLayerLocators.INPUT_street_number, receiver_data["street_number"])
        self.send_keys(NewReceiverCourierLayerLocators.INPUT_post_code, receiver_data["postal_code"])
        if self.wait_for.element_visible(
                NewReceiverCourierLayerLocators.ELEMENT_city_autofilled, raise_exception=False):
            self.wait_for.element_visible(NewReceiverCourierLayerLocators.DROPDOWN_extend_cities).click()
            city = self.wait_for.element_visible(
                NewReceiverCourierLayerLocators.INPUT_city.format(
                    city_name=receiver_data["city"]), raise_exception=False)
            if city:
                city.click()
        self.send_keys(NewReceiverCourierLayerLocators.INPUT_phone, receiver_data["phone"])
        self.send_keys(NewReceiverCourierLayerLocators.INPUT_email, receiver_data["mail"])
        add_btn = self.wait_for.element_visible(
            NewReceiverCourierLayerLocators.BUTTON_add_receiver, raise_exception=False)
        if add_btn:
            add_btn.click(self.TIMEOUT_NUXT_TOASTS)
        elif not self.element_visibility.get_element_visibility(NewPrivatePurchaserLayerLocators.SELECT_city):
            pass


class CommonPurchaserReceiverLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def compare_errors_new_purchaser_receiver_form(self, test_data: dict, form_type: str):
        if form_type == "purchaser":
            error_messages = test_data["purchaser_object"]["purchaser_data_errors"]
            if (test_data["purchaser_object"]["purchaser_type"] == PurchaserKey.COMPANY and
                    test_data["purchaser_object"]["purchaser_data"]["country"] == "Kanada"):
                error_messages["postal_code"] = "Niepoprawny kod"
                error_messages["phone"] = "Podaj właściwy numer"
        else:
            error_messages = test_data["delivery_object"]["receiver_data_errors"]
        error_messages_in_form = {}
        for key, value in CommonPurchaserReceiverErrorsLayerLocators.forms_error_messages().items():
            if self.element_visibility.get_element_visibility(value):
                self.time.sleep(1)
                error_messages_in_form[key] = self.wait_for.element_visible(value).text

        for key in error_messages_in_form:
            if key not in ["phone_code"]:
                actual = error_messages_in_form[key]
                expected = error_messages[key]
                assert actual == expected, f"Actual error {actual} is not equal to expected error {expected}"


class LayerPromotionsObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def close_layer_if_visible(self):
        close_layer_btn = self.wait_for.element_visible(
            LayerWithPromotionsLocators.BUTTON_close, raise_exception=False)
        if close_layer_btn:
            self.wait_for_attribute_disappear(close_layer_btn)
            close_layer_btn.click()

    def select_promotion_by_name(self, promotion_name: str):
        pagination_promo = self.wait_for.element_visible(
            LayerWithPromotionsLocators.ELEMENT_pagination_promo.format(promotion_title=promotion_name),
            raise_exception=False,
        )
        if pagination_promo:
            self.click_element(pagination_promo)
        self.click_element(self.wait_for.element_visible(
            LayerWithPromotionsLocators.BUTTON_select_promotion.format(promotion_title=promotion_name)),
            sleep_time=self.TIMEOUT_SHORT)
        self.wait_for.element_invisible(LayerWithPromotionsLocators.ELEMENT_layer_title)


class AfterRegisterLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)


class LayerSummaryObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)
        self.locator = SummaryCartLayerLocators()

    def click_go_to_cart(self, timeout: int | None = None):
        wait_timeout = timeout if timeout else self.TIMEOUT_SHORT
        if not self.wait_for.element_visible(self.locator.BUTTON_go_to_cart, raise_exception=False, timeout=wait_timeout):
            return

        buttons = self.driver.locator(self.locator.BUTTON_go_to_cart)
        for idx in range(buttons.count()):
            button = buttons.nth(idx)
            if button.is_visible():
                button.wait_for(state="visible", timeout=int(self.TIMEOUT_LONG * 1000))
                button.click()
                return


class AfterLoginLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)


class LogoutLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)


class MontageLayerObject(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def apply_montage_changes(self, pc_montage: bool):
        self.wait_for.element_visible(MontageLayerLocators.CONTAINER_layer)
        if pc_montage:
            self.wait_for.element_visible(MontageLayerLocators.BUTTON_apply_changes).click()
        self.wait_for.element_invisible(MontageLayerLocators.CONTAINER_layer)


class OpinionLayerObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def close_layer(self):
        self.wait_for.element_visible(OpinionLayerLocators.BUTTON_close).click()


class LayerProductsAddedToCompareObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def close_layer(self):
        self.wait_for.element_visible(LayerProductsAddedToCompareLocators.BUTTON_close).click(
            self.TIMEOUT_NUXT_TOASTS)

    def compare_products(self):
        self.wait_for.element_visible(LayerProductsAddedToCompareLocators.BUTTON_compare_now).click()
        assert self.wait_for.element_visible(LayerProductsAddedToCompareLocators.ELEMENT_products_comparison,
                                             raise_exception=False)


class LayerWithStorehouseAvailability(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def get_storehouses_availability_details(self) -> list[list[str]]:
        self.wait_for.element_visible(LayerWithStorehouseAvailabilityLocators.CONTAINER_layer)
        self.wait_for.element_visible(LayerWithStorehouseAvailabilityLocators.BUTTON_show_details).click()
        self.wait_for.element_visible(LayerWithStorehouseAvailabilityLocators.CONTAINER_storehouses_list)
        storehouses = self.driver.locator(LayerWithStorehouseAvailabilityLocators.ELEMENTS_storehouses)
        return [storehouses.nth(idx).inner_text().splitlines() for idx in range(storehouses.count())]


class LayerWithProductAvailability(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)


class LayerWithProductNewsletter(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def sign_to_newsletter(self, email: str):
        self.wait_for.element_visible(ProductNewsletterLayerLocators.ELEMENT_title)
        self.send_keys(self.wait_for.element_visible(ProductNewsletterLayerLocators.INPUT_email), email)
        self.wait_for.element_visible(ProductNewsletterLayerLocators.CHECKBOX_terms).click()
        self.wait_for.element_visible(ProductNewsletterLayerLocators.BUTTON_sign_in).click()


class LayerWithProductRecommendationPageObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def skip_recommendation_layer_if_visible(self):
        recommendation_layer = self.wait_for.element_visible(
            LayerWithProductRecommendation.ELEMENT_layer_title,
            raise_exception=False,
        )
        if recommendation_layer:
            self.wait_for.element_visible(LayerWithProductRecommendation.BUTTON_close).click()


class LayerWishlistOnProductPageObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def create_new_wishlist_on_product_page(self, list_name):
        self.wait_for.element_visible(WishlistLayerLocators.BUTTON_create_new_wishlist).click()
        self.wait_for.element_visible(WishlistLayerLocators.INPUT_wishlist_name).send_keys(list_name)
        self.wait_for.element_visible(WishlistLayerLocators.BUTTON_create_wishlist).click()
        self.wait_for.element_visible(WishlistLayerLocators.INPUT_wishlist_checkbox).click()
        self.wait_for.element_visible(WishlistLayerLocators.BUTTON_add_product_to_wishlist).click()
        self.wait_for.element_visible(WishlistLayerLocators.BUTTON_go_to_wishlist).click()


class LayerWishlistOnWishlistSummaryPage(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def create_new_wishlist_on_wishlist_summary_page(self, list_name):
        self.wait_for.element_visible(WishlistLayerLocators.INPUT_wishlist_name).send_keys(list_name)
        self.wait_for.element_visible(WishlistLayerLocators.BUTTON_create_wishlist).click()

    def confirm_delete_on_wishlist_summary_page_layer(self):
        self.wait_for.element_visible(WishlistLayerLocators.BUTTON_delete_wishlist).click()
