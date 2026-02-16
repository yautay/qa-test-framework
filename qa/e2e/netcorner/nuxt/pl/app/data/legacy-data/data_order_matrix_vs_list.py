import copy

from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario = "Scenariusz: \n" \
           "   1. Otwiera stronę panelu administracyjnego i loguje się.\n" \
           "   2. Weryfikuje konfigurację zmiennej 'enforce_shopping_path_post_codes'.\n" \
           "   3. Otwiera stronę główną, wyszukuje produkt i dodaje go do koszyka.\n" \
           "   4. W procesie zamówienia podaje zapamiętany kod i sprawdza czy dla kodu aktywowała się lista lub macierz" \
           " z terminami dostaw.\n"

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()},
    "category": CommonData.url_product_list()["laptops_casual"],
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}

order_matrix = {

    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "matrix": True,
                        "receiver_data": PlCommonData.receiver_data_postcode_matrix(),
                        "receiver_type": ReceiverKey.PRIVATE
                        },
}
order_matrix.update(copy.deepcopy(common_test_data))
order_matrix.setdefault("scenario", scenario)

order_list = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "matrix": False,
                        "receiver_data": PlCommonData.receiver_data_postcode_list(),
                        "receiver_type": ReceiverKey.PRIVATE
                        },
}
order_list.update(copy.deepcopy(common_test_data))
order_list.setdefault("scenario", scenario)
