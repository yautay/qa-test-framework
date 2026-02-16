from TestCases.NetCornerProducts.Common.PageLocators.CommonAdminLocators import CommonAdminLocators


class AggregatorLocators:
    CONTAINER = CommonAdminLocators.CONTAINER_product_page
    HEADER_aggregator = "//div[@data-name='aggregatorSlider']//div[contains(@class, 'swiper-initialized')]"
    HEADER_img_product = "//img[contains(@alt, 'Logitech')]"
    ELEMENT_agregator_product = "//div[@data-name='cardProduct']"
    BUTTON_buy_product = "//button[contains(text(), 'Sprawdź')]"
    BUTTON_buy_product_in_card = ".//button[contains(text(), 'Sprawdź')]"
    BUTTON_import_csv = "//input[@id='ktr_promotion_aggregator_item_product_codes_import']"
    COMPONENT_aggregator_product = "//div[@data-name='cardProduct']"
