from typing import Any

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib import PageLocators as Locators
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib import PageObjects as Page
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    OrderAsKey,
    ProductKey,
    ProductPageAlertKey,
)


class FunctionalObjects(CommonPO):
    def __init__(self, driver):
        super().__init__(driver)

    def select_test_product(self, base_url: str, category: str or list, filters: list = None, add_to_cart: bool = True,
                            with_lift: bool = False, digital: bool = False, temporarily_unavailable: bool = False,
                            product_page_function: CommonPO.CallableCommon = None) -> Any:
        def logic(_category: str, _filters: dict or None) -> dict or None:
            with self.perf_step("select_test_product", meta={"category": _category, "digital": digital}):
                self.driver.get(base_url + _category)
                return Page.SelectTestProductFromProductListObject(self.driver).get_test_product(filters=_filters,
                                                                                                 add_to_cart=add_to_cart,
                                                                                                 with_lift=with_lift,
                                                                                                 digital=digital,
                                                                                                 temporarily_unavailable=temporarily_unavailable,
                                                                                                 product_page_function=product_page_function)

        if type(category) is not list:
            return logic(category, filters)
        else:
            results = []
            for x in range(len(category)):
                results.append(logic(category[x], filters[x]) if filters else logic(category[x], None))
            return results

    def add_product_to_cart(self, base_url: str,
                            product: ProductKey | CommonPO.ListCommon[ProductKey] | int | CommonPO.ListCommon[int],
                            product_page_function: CommonPO.CallableCommon = None) -> dict | ProductPageAlertKey | None:
        def __add_product() -> dict or ProductPageAlertKey:
            Page.LayerWithProductRecommendationPageObjects(self.driver).skip_recommendation_layer_if_visible()
            function_return = product_page_function() if product_page_function else None
            Page.ProductPageObjects(self.driver).action_click_add_to_cart()
            alert = Page.ProductPageObjects(self.driver).check_alert()
            if alert:
                return alert
            Page.LayerPromotionsObject(self.driver).close_layer_if_visible()
            Page.LayerSummaryObject(self.driver).click_go_to_cart()
            return function_return

        def __get_product_by_id(_p: int) -> dict:
            self.driver.get(base_url + f"product/{_p}")
            return {_p: __add_product()}

        def __get_product_by_key(_p: ProductKey) -> dict:
            self.driver.get(base_url)
            Page.SearchObjects(self.driver).search_phrase(_p.value)
            return {_p: __add_product()}

        def get_product(_p) -> dict:
            if type(_p) is int:
                return __get_product_by_id(_p)
            if issubclass(_p.__class__, ProductKey):
                return __get_product_by_key(_p)
            else:
                raise ValueError("Unsupported product type")

        if isinstance(product, list):
            return_data = {}
            with self.perf_step("add_product_to_cart_batch", meta={"count": len(product)}):
                for p in product:
                    product = get_product(p)
                    if product:
                        return_data.update({p: product})
            return return_data
        else:
            with self.perf_step("add_product_to_cart"):
                return get_product(product)

    def register_customer_if_required(self, driver, test_data: dict, register_from_login_layer: bool = False) -> bool:
        def log_user():
            self.time.sleep(self.TIMEOUT_SHORT)
            header = Page.HeaderObjects(driver)
            login_layer = Page.LoginLayerObject(driver)
            header.enter_login_layer()
            if not login_layer.login_layer_visibility():
                self.time.sleep(1)
                header.enter_login_layer()
            login_layer.login_user(test_data["register_data"])
            self.time.sleep(self.TIMEOUT_NUXT_TOASTS)

        with self.perf_step("register_customer_if_required"):
            if "order_as" not in test_data.keys():
                order_as = OrderAsKey.ORDER_AS_REGISTERED
            else:
                order_as = test_data["order_as"]

            if order_as == OrderAsKey.JUST_LOG_USER:
                log_user()

            elif order_as in [OrderAsKey.ORDER_AS_LOGGED_IN_CART_SKIP_REGISTRATION, OrderAsKey.ORDER_AS_NON_REGISTERED]:
                pass

            else:
                login_layer = Page.LoginLayerObject(driver)
                if not register_from_login_layer:
                    header = Page.HeaderObjects(driver)
                    header.enter_login_layer()
                    if not login_layer.login_layer_visibility():
                        self.time.sleep(1)
                        header.enter_login_layer()
                login_layer.enter_register_form()
                registered_new_user = Page.RegisterObjects(driver).register_new_customer(test_data)
                if not registered_new_user:
                    log_user()
                if order_as == OrderAsKey.ORDER_AS_LOGGED_IN_CART:
                    Page.HeaderObjects(driver).logout_user()
                return registered_new_user

    def add_product_to_cart_and_check_promo(self, test_data: dict, category_url_element: str, base_url: str):
        def product_function():
            test_data["product_page_data"] = Page.ProductPageObjects(self.driver).get_crossed_out_price()
            return test_data["product_page_data"]
        category_url = "category/" + str(category_url_element)
        self.select_test_product(base_url, category=category_url, product_page_function=product_function)

    def process_order_init_checkout(self, test_data: dict,
                                    cart_function: CommonPO.CallableCommon = None) -> dict | None:
        with self.perf_step("checkout_init"):
            if self.wait_for.element_visible(Locators.SummaryCartLayerLocators.BUTTON_go_to_cart,
                                             timeout=self.TIMEOUT_SHORT, raise_exception=False):
                Page.LayerSummaryObject(self.driver).click_go_to_cart()
            cart_function_return = cart_function() if cart_function else None
            Page.CartObjects(self.driver).click_move_further()
            login_layer = Page.LoginLayerObject(self.driver)
            if test_data["order_as"] != OrderAsKey.ORDER_AS_NON_REGISTERED:
                login_layer.login_user(test_data["register_data"])
            else:
                login_layer.click_order_without_registration()
            return cart_function_return

    def process_order_checkout_core(self, test_data: dict):
        with self.perf_step("checkout_core"):
            Page.ChooseDeliveryMethodObjects(self.driver).select_delivery_method(test_data)
            Page.CheckoutReceiverObjectsFactory(self.driver, test_data).add_new_receiver_object()
            Page.CheckoutPurchaserObjectsFactory(self.driver, test_data).add_new_purchaser_object()
            Page.CheckoutPaymentObjects(self.driver).select_payment(test_data)

    def process_order_complete_checkout(self, test_data: dict, submit_order: bool = True, add_comment: bool = False):
        with self.perf_step("checkout_complete", meta={"submit_order": submit_order}):
            checkout_objects = Page.CheckoutObjects(self.driver)
            if add_comment:
                checkout_objects.add_comment_to_order(test_data["comment_to_order"])
            checkout_objects.accept_terms()
            checkout_objects.accept_terms_digital()
            checkout_objects.accept_terms_mca_license()
            if submit_order:
                checkout_objects.submit_order()

    def process_order_full_checkout(self, test_data: dict, submit_order: bool = True,
                                    add_comment: bool = False,
                                    cart_callable: CommonPO.CallableCommon = None) -> dict | None:
        cart_function_return = self.process_order_init_checkout(test_data, cart_function=cart_callable)
        self.process_order_checkout_core(test_data)
        self.process_order_complete_checkout(test_data, submit_order, add_comment)
        return cart_function_return

    def enter_specific_order_summary(self, base_url, order_data):
        self.driver.get(base_url)
        Page.HeaderObjects(self.driver).enter_my_account()
        Page.MyAccountObjects(self.driver).enter_orders_summary()
        Page.MyAccountOrderSummary(self.driver).enter_order_summary(order_data["order_number"])
