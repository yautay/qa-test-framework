from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    FrontTestProductsKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
)

scenario = "Scenariusz: \n" \
           "   1. Otwiera stronę z produktem i dodaje produkt do koszyka.\n" \
           "   2. Składa zamówienie z danymi dla odbiorcy i typem płatności.\n" \
           "   3. Sprawdza czy produkt posiada minimalną ilość sztuk wymaganą dla danego produktu."

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "scenario": scenario,
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.MIN_QTY_PRODUCT],
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "delivery_location": PlCommonData.cart_variables()["delivery_location_postal_60001"],
                        "delivery_point_name": PlCommonData.cart_variables(
                            test_storehouses=True)["delivery_point_name_poznan_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
data_order_with_min_qty_product_1 = {
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.MIN_QTY_PRODUCT],
}
data_order_with_min_qty_product_2 = {
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.MIN_QTY_PRODUCT_W_UNIT_PRICE],
}

data_order_with_min_qty_product_1.update(common_test_data.copy())
data_order_with_min_qty_product_2.update(common_test_data.copy())
