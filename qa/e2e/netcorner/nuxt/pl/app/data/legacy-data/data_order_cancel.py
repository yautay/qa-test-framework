from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario = "Scenariusz: \n" \
           "   1. Dodaje produkt.\n" \
           "   2. Przechodzi do koszyka i się loguje.\n" \
           "   3. Składa zamówienie.\n" \
           "   4. Przechodzi do historii zamówień po stronie klienta.\n" \
           "   5. Przechodzi do szczegółów zamówienia.\n" \
           "   6. Klika w przycisk anulowania zamówienia."

pl_var = PlCommonData.variables(test_storehouses=True)

order_cancel = {
    "register_data": PlCommonData.common_client(),
    "order_as": OrderAsKey.JUST_LOG_USER,
    "category": CommonData.url_product_list()["keyboards"],
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "submit_order":True
}
order_cancel.setdefault("scenario", scenario)

