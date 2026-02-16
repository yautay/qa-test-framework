import copy

from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMatrixKey,
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_delivery_at_home = "Scenariusz: \n" \
                            "   1. Otwiera stronę z produktem powyżej 15000 PLN jako niezarejestrowany klient.\n" \
                            "   2. Dodaje produkt do koszyka.\n" \
                            "   3. Klika w przycisk 'Zamów z dostawą'.\n" \
                            "   4. Wypełnia formularz odbiorcy, wybiera pierwszy dostępny dzień z macierzy." \
                            " Kopiuje dane do formularza nabywcy i wybiera metodę płatności.\n" \
                            "   5. Wpisuje Poznań w lokalizacje i wybiera Poznań Outlet, wypełnia formularz " \
                            "nabywcy i wybiera metodę płatności.\n" \
                            "   6. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_self_pickup = "Scenariusz: \n" \
                       "   1. Otwiera stronę z produktem powyżej 15000 PLN jako niezarejestrowany klient.\n" \
                       "   2. Dodaje produkt do koszyka.\n" \
                       "   3. Klika w przycisk 'Zamów z odbiorem osobistym'.\n" \
                       "   4. Wpisuje Poznań w lokalizacje i wybiera Poznań Outlet, wypełnia formularz nabywcy " \
                       "i wybiera metodę płatności.\n" \
                       "   5. Składa zamówienie i czeka na pojawienie się thank you page."

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "category": CommonData.url_product_list()["laptops_expensive"],
    "register_data": PlCommonData.register_data(),
    "purchaser_object": {"order_as": PurchaserKey.COMPANY,
                         "purchaser_data": PlCommonData.purchaser_data_gus()},
    "payment_option": PaymentKey.SPLIT_PAYMENT,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}

delivery_at_home_split_payment = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.COMPANY,
                        "matrix_tile_price_limit": DeliveryMatrixKey.FREE}
}

self_pickup_split_payment = {
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "delivery_location": pl_var["delivery_city_poznan"],
                        "delivery_point_name": pl_var["delivery_point_saloon"]},
}

delivery_at_home_split_payment.update(copy.deepcopy(common_test_data))
self_pickup_split_payment.update(copy.deepcopy(common_test_data))

delivery_at_home_split_payment.setdefault("scenario", scenario_delivery_at_home)
self_pickup_split_payment.setdefault("scenario", scenario_self_pickup)
