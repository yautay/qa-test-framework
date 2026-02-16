class CartLocators:
    CONTAINER_per_product = "//div[@data-product-id]"
    ELEMENT_cart_step_selector = "//span[contains(text(), 'Twój koszyk')]"
    ELEMENT_product_quantity_by_product_index = "//div[contains(text(),'{}')]/..//div[contains(@class,'control__input')]/"
    BUTTON_move_further = "//button[contains(., 'Przejdź dalej')]"
    BUTTON_move_further_enabled = "bg-blue-smalt"
    CONTAINER_product_row_by_id = "//div[@data-product-id='{product_id}']"
    ELEMENT_product_price_gross = CONTAINER_product_row_by_id + "//div[@data-name='cartProductPrice']/p[@data-price-type='gross']"
    ELEMENT_product_price_total = CONTAINER_product_row_by_id + "//div[@data-name='cartProductTotal']/p[@data-price-type='gross']"
    CONTAINER_quantity = CONTAINER_product_row_by_id + "//div[@data-role='qtyPicker']"
    INPUT_product_quantity = CONTAINER_quantity + "/input"
    BUTTON_product_quantity_increase = CONTAINER_quantity + "//i[@class='i-plus']/ancestor::button"
    BUTTON_product_quantity_decrease = CONTAINER_quantity + "//i[@class='i-minus']/ancestor::button"
    ELEMENT_cart_value = "//p[contains(text(), 'Wartość produktów')]/following-sibling::div/p[contains(@class, 'font-semibold')]"
    ELEMENT_alert = "//*[@data-name='cartMainAlert']/*[contains(text(), '{alert_msg}')]"
    TOAST_cart = "//li[contains(@class, 'toast-negative')]//div"
    INPUT_promo_code = "//input[@id='couponCode']"
    BUTTON_add_promo_code = "//div[contains(text(), 'Dodaj kod')]/ancestor::button"
    ELEMENT_added_code = "//p[text()='{code}']"
    BUTTON_empty_cart = "//button[contains(., 'Wyczyść koszyk')]"
    ELEMENT_product_name = "//div[@data-name='cartProductMain']//div//a"


class CartProductContainerLocators(CartLocators):
    ELEMENT_price_base = "//del[@data-price-type='base']"
    ELEMENTS_price_gross = "//p[@data-price-type='gross']"
    ELEMENT_price_omnibus = "//span[@data-price-type='omnibus']"
    ELEMENT_qty = "//input[@type='number']"
    ELEMENT_limited_sale_banner = "//p[contains(text(), 'Sprzedaż limitowana')]"


class CartOfferLocators:
    ELEMENT_offer_price = "//div[@data-name='offerTotalValue']"
    BUTTON_add_offer_to_cart = "//button[contains(., 'Dodaj wszystko do koszyka')]"
