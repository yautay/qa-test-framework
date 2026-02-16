from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

from .PlCommonData import PlCommonData

scenario = "Scenariusz: \n" \
           "   1. Wchodzi na stronę produktu i dodaje go do koszyka.\n" \
           "   2. Wybiera zamówienie z dostawą do domu.\n" \
           "   3. Składa zamówienie z danymi odbiorcy.\n" \
           "   4. Przechodzi na stronę szczegółów zamówienia w adminie zmienia status." \
           "   5. Sprawdza czy na stronie szczegółów zamówienia użytkownika zmienił się status."

pl_var = PlCommonData.variables(test_storehouses=True)

order_statuses = {
    "register_data": PlCommonData.common_client(),
    "order_as": OrderAsKey.JUST_LOG_USER,
    "category": CommonData.url_product_list()["keyboards"],
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "admin_message": CommonData.messages_and_dictionaries()["admin_cancelled"],
    "statuses": {
        "2": "W trakcie przetwarzania",
        "3": "Czekamy na wpłatę",
        "4": "Przekazano do wysyłki",
        "5": "Wysłane",
        "6": "Odebrane osobiście",
        "7": "Gotowe do odbioru",
        "1": "Nowe",
        "0": "Anulowane"
    },
}
order_statuses.setdefault("scenario", scenario)
