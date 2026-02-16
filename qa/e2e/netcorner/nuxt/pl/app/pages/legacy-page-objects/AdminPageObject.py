from TestCases.NetCornerProducts.admin_panel.Lib import PageObjects as AdminPage
from TestCases.NetCornerProducts.admin_panel.Lib.PageLocators import ProductTabLocators
from TestCases.NetCornerProducts.admin_panel.Lib.PageObjects import CartOfferObjects
from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject


class AdminOrdersObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def assert_admin_order_details(self, admin_ulr: str, test_data: dict) -> dict:
        with self.perf_step("admin_verify_order"):
            AdminPage.AdminFunctionalObjects(self.driver).open_admin_resource(admin_ulr, "orders/list/pl")
            AdminPage.OrdersListObjects(self.driver).click_order_link(test_data["typ_data"]["order_number"])
            test_data["typ_data"]["admin_order_url"] = self.driver.current_url
            page = AdminPage.OrderPageObjects(self.driver)
            if "typ_data" in test_data.keys():
                page.assert_summary_price(test_data["typ_data"]["summary_price"])
            if "warehouse" in test_data["delivery_object"].keys():
                page.assert_order_param("Magazyn", test_data["delivery_object"]["warehouse"])
            if "order_with" in test_data["delivery_object"].keys():
                page.assert_order_param("Metoda transportu", test_data["delivery_object"]["order_with"])
            return page.get_order_page_data()


class AdminPromoCodesObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def login_to_admin_panel(self, admin_url: str):
        self.driver.get(admin_url)
        AdminPage.LoginAdmin(self.driver).perform_login()

    def create_promo_codes(self, admin_url: str):
        self.login_to_admin_panel(admin_url)
        self.driver.get(self.driver.current_url + "codePromotionService/list/pl")
        AdminPage.CreateTestPromoCodes(self.driver).create_test_promo_codes()

    def create_aggregator_promo_codes(self, admin_url: str, test_data: dict):
        self.login_to_admin_panel(admin_url)
        self.driver.get(self.driver.current_url + "promotionAggregator/list/pl")
        AdminPage.AggregatorObjects(self.driver).click_create_aggregator()
        AdminPage.FillNewAggregatorForm(self.driver).fill_aggregator_form(test_data["aggregator_data"])
        if AdminPage.FillNewAggregatorForm(self.driver).save_changes():
            AdminPage.AggregatorObjects(self.driver).create_new_element()
            if "category" in test_data.__name__:
                AdminPage.FillNewAggregatorElementFormCategory(self.driver, test_data["aggregator_element_data"])
            else:
                AdminPage.FillNewAggregatorElementFormProducts(self.driver, test_data["aggregator_element_data"])
            AdminPage.AggregatorObjects(self.driver).save_changes()
        AdminPage.AggregatorObjects(self.driver).return_to_aggregator()


class AdminProductPageObjects(CommonBasePageObject):
    def __init__(self, driver):
        super().__init__(driver)

    def save_test_promotions(self):
        promotions_tab_objects = AdminPage.PromotionsTabObjects(self.driver)
        promotions_tab_objects.enter_promotion_tab()
        promotions_tab_objects.save_existing_promotions()

    def save_test_product(self):
        button_save = self.wait_for.element_visible(ProductTabLocators.BUTTON_save_product)
        self.click_element(button_save)


class AdminPageObjects(AdminOrdersObjects, AdminPromoCodesObjects, AdminProductPageObjects, CartOfferObjects):
    def __init__(self, driver):
        super().__init__(driver)
