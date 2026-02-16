from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
    WcrProductKey,
)

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_wcr_products = PlCommonData.wcr_products()
pl_var = PlCommonData.variables()
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

scenario = "Confluence - \"Ograniczenia koszyka - testy automatyczne\"\n" \
           "Scenariusz:" \
           "   Produkt ND/DW z flagą WCR\n" \
           "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
           "   2. Zwiększa ilość do 2 produktów.\n" \
           "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny.\n" \
           "   4. Automat przechodzi przez proces zakupowy.\n"

common_test_data = {
    "scenario": scenario,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "purchaser_object": {
        "order_as": PurchaserKey.PRIVATE,
        "purchaser_data": PlCommonData.purchaser_data()},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}

product_wcr_nd_stock = {
    "product_code": pl_wcr_products[WcrProductKey.WCR_ND_STOCK],
    "availability_status": pl_var["order_status_one_work_day"]
}

product_wcr_dw_stock = {
    "product_code": pl_wcr_products[WcrProductKey.WCR_DW_STOCK],
    "availability_status": pl_var["order_status_one_work_day"]
}

product_wcr_nd = {
    "product_code": pl_wcr_products[WcrProductKey.WCR_ND],
    "availability_status": pl_var["order_status_wcr"]
}

product_wcr_dw = {
    "product_code": pl_wcr_products[WcrProductKey.WCR_DW],
    "availability_status": pl_var["order_status_wcr"]
}

product_wcr_nd_stock.update(common_test_data.copy())
product_wcr_dw_stock.update(common_test_data.copy())
product_wcr_nd.update(common_test_data.copy())
product_wcr_dw.update(common_test_data.copy())
