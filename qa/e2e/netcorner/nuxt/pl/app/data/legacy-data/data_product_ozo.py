from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    FrontTestProductsKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_ozo_visibility = "Scenariusz: \n" \
                          "   1. Weryfikuje widoczność produktu OzO na Stronie głównej.\n"

scenario_limited_sale_visibility = "Scenariusz: \n" \
                                   "   1. Weryfikuje widoczność produktu SL na karcie produktu.\n"

scenario_limited_sale_cart_restrictions = "Scenariusz: \n" \
                                          "   1. Weryfikuje widoczność SL w koszyku.\n" \
                                          "   2. Weryfikuje ograniczenia ilościowe SL w koszyku.\n"

scenario_ozo_parameters = "Scenariusz: \n" \
                          "   1. Weryfikuje takie parametry boksu OzO jak:\n" \
                          "     a. Czy zegar pokazuje poprawny czas do końca oferty OzO.\n" \
                          "     b. Czy liczba sztuk pozostałych do sprzedaży jest poprawna."

scenario_ozo_limited_sale = "Scenariusz: \n" \
                            "   1. Weryfikuje działanie mechanizmu SL dla produktu OzO oraz aktualizowanie paska statusu"

scenario_ozo_limited_sale_logged_client = "Scenariusz: \n" \
                                          "   1. Weryfikuje działanie limitu SL dla klienta zalogowanego"

scenario_ozo_limited_sale_guest_client = "Scenariusz: \n" \
                                         "   1. Weryfikuje działanie limitu SL dla klienta nie zalogowanego"

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "register_data": PlCommonData.register_data(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}

data_ozo_visibility = {
    "scenario": scenario_ozo_visibility
}
data_limited_sale_visibility = {
    "scenario": scenario_limited_sale_visibility,
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.OZO_PRODUCT]
}
data_limited_sale_cart_restrictions = {
    "scenario": scenario_limited_sale_cart_restrictions,
    "register_data": PlCommonData.register_data(),
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.OZO_PRODUCT]
}
data_ozo_parameters = {
    "scenario": scenario_ozo_parameters,
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.OZO_PRODUCT]
}
data_ozo_limited_sale = {
    "scenario": scenario_ozo_limited_sale,
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.OZO_PRODUCT],
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
data_ozo_limited_sale.update(common_test_data.copy())

data_limited_sale_logged_client = {
    "scenario": scenario_ozo_limited_sale_logged_client,
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.OZO_PRODUCT],
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
data_limited_sale_logged_client.update(common_test_data.copy())

data_limited_sale_guest_client = {
    "scenario": scenario_ozo_limited_sale_guest_client,
    "product_id": PlCommonData.front_test_products()[FrontTestProductsKey.OZO_PRODUCT],
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
data_limited_sale_guest_client.update(common_test_data.copy())
