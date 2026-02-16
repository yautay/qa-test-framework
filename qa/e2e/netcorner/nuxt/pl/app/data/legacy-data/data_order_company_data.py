from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario = "Scenariusz: \n" \
           "   1. Wchodzi na stronę produktu i dodaje go do koszyka.\n" \
           "   2. Wybiera zamówienie z dostawą do domu.\n" \
           "   3. Składa zamówienie z danymi odbiorcy jako FIRMA.\n" \
           "   4. Przechodzi na stronę szczegółami zamówienia (uzytkownik i admin)," \
           "       sprawdza czy cen podsumowująca zgadza się z oczekiwaną.\n" \
           "   5. W adminie weryfikuje dane nabywcy FIRMOWEGO."

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "scenario": scenario,
    "register_data": PlCommonData.register_data(),
    "category": CommonData.url_product_list()["keyboards"],
    "purchaser_object": {"order_as": PurchaserKey.COMPANY,
                         "purchaser_data": PlCommonData.purchaser_data_gus()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.COMPANY},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
data_order_company_data_registered = {
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,

}
data_order_company_data_not_registered = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
data_order_company_data_registered.update(common_test_data.copy())
data_order_company_data_not_registered.update(common_test_data.copy())
