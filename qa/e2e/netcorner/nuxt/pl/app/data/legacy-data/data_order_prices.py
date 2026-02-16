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
           "   3. Składa zamówienie z danymi odbiorcy.\n" \
           "   4. Przechodzi na stronę szczegółami zamówienia (uzytkownik i admin)," \
           "       sprawdza czy cen podsumowująca zgadza się z oczekiwaną."

pl_var = PlCommonData.variables(test_storehouses=True)

order_prices = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "category": CommonData.url_product_list()["keyboards"],
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
order_prices.setdefault("scenario", scenario)
