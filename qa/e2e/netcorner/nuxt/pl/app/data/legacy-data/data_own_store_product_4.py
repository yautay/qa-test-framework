from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 4.1, 4.2\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Zwiększa ilość produktów do 2 sztuk i sprawdza czy wyświetlił się odpowiedni alert.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   4. Sprawdza czy przycisk KURIER, SALON są aktywne.\n" \
            "   5. Klika w KURIER.\n" \
            "   6. Uzupełnia wszystkie dane i sprawdza czy na pewno nie pojawila sie macierz, składa zamowienia.\n" \
            "   7. Sprawdza czy w szczegółach zamówienia (moje konto) składają się wszystkie dane.\n" \
            "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz czy magazyn " \
            "jest poprawny."

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 4.3, 4.4, 4.5, 4.6, 4.7\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy oba przyciski sa aktywne, wybiera z odbiorem osobistym.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   4. Sprawdza czy przycisk KURIER, SALON są aktywne.\n" \
            "   5. Klika w SALON.\n" \
            "   6. Wybiera punkt odbioru i składa zamówienie.\n" \
            "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz czy magazyn " \
            "jest poprawny."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_4_dw_send_from_store = {
    "product_number": pl_cart_var["product_number_04"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_4_dw_send_from_store.update(common_test_data.copy())
product_4_dw_send_from_store.setdefault("scenario", scenario1)

product_4_nd_send_from_store = {
    "product_number": pl_cart_var["product_number_04"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_4_nd_send_from_store.update(common_test_data.copy())
product_4_nd_send_from_store.setdefault("scenario", scenario1)

product_4_dw_pickup_from_warszawa_megastore = {
    "product_number": pl_cart_var["product_number_04"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_pruszkow"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": None},
                        ]},
    "payment_option": PaymentKey.CASH
}
product_4_dw_pickup_from_warszawa_megastore.update(common_test_data.copy())
product_4_dw_pickup_from_warszawa_megastore.setdefault("scenario", scenario2)

product_4_nd_pickup_from_warszawa_megastore = {
    "product_number": pl_cart_var["product_number_04"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_pruszkow"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": None},
                        ]},
    "payment_option": PaymentKey.CASH
}
product_4_nd_pickup_from_warszawa_megastore.update(common_test_data.copy())
product_4_nd_pickup_from_warszawa_megastore.setdefault("scenario", scenario2)

product_4_dw_pickup_from_stary_browar = {
    "product_number": pl_cart_var["product_number_04"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": None},
                        ]},
    "payment_option": PaymentKey.CASH
}
product_4_dw_pickup_from_stary_browar.update(common_test_data.copy())
product_4_dw_pickup_from_stary_browar.setdefault("scenario", scenario2)

product_4_nd_pickup_from_stary_browar = {
    "product_number": pl_cart_var["product_number_04"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": None},
                        ]},
    "payment_option": PaymentKey.CASH
}
product_4_nd_pickup_from_stary_browar.update(common_test_data.copy())
product_4_nd_pickup_from_stary_browar.setdefault("scenario", scenario2)
