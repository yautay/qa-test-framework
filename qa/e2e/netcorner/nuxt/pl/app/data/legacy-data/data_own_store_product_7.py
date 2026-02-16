from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    AlertKey,
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 7.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Zwiększa ilość do 4 produktów.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny.\n"

scenario2_amount_1 = "Scenariusz: \n" \
                     "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 7.2, 7.3\"\n" \
                     "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                     "   2. Ustawia ilość produktu na 1.\n" \
                     "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                     "   4. Sprawdza czy przycisk KURIER, SALON są aktywne.\n" \
                     "   5. Wybiera metodę KURIER.\n" \
                     "   6. Uzupełnia wszystkie dane, sprawdza czy lista dostaw jest niewidoczna i składa zamówienie.\n" \
                     "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                     "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
                     "oraz czy magazyn to Magazyn Główny."

scenario2_amount_2 = "Scenariusz: \n" \
                     "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 7.2, 7.3\"\n" \
                     "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                     "   2. Ustawia ilość produktu na 2.\n" \
                     "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                     "   4. Sprawdza czy przycisk KURIER, SALON są aktywne.\n" \
                     "   5. Wybiera metodę KURIER.\n" \
                     "   6. Uzupełnia wszystkie dane, sprawdza czy macierz jest niewidoczna i składa zamówienie.\n" \
                     "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                     "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
                     "oraz czy magazyn to Magazyn Główny."

scenario3_amount_1 = "Scenariusz: \n" \
                     "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 7.4, 7.5, 7.6, 7.7, 7.8," \
                     " 7.9, 7.10, 7.11, 7.12, 7.13\"\n" \
                     "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                     "   2. Zwiększa ilość produktów do 1.\n" \
                     "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                     "   4. Sprawdza czy przyciski metod transportu są aktywne.\n" \
                     "   5. Wybiera metodę transportu.\n" \
                     "   6. Wyszukuje miasto i sprawdza komunikat.\n" \
                     "   7. Wybiera punkt odbioru i składa zamówienie.\n" \
                     "   8. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                     "   9. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz" \
                     " czy magazyn jest poprawny."

scenario3_amount_2 = "Scenariusz: \n" \
                     "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 7.4, 7.5, 7.6, 7.7, 7.8," \
                     " 7.9, 7.10, 7.11, 7.12, 7.13\"\n" \
                     "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                     "   2. Zwiększa ilość produktów do 2.\n" \
                     "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                     "   4. Sprawdza czy przyciski metod transportu są aktywne.\n" \
                     "   5. Wybiera metodę transportu.\n" \
                     "   6. Wyszukuje miasto i sprawdza komunikat.\n" \
                     "   7. Wybiera punkt odbioru i składa zamówienie.\n" \
                     "   8. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                     "   9. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz" \
                     " czy magazyn jest poprawny."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_7_dw = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "alert_type": AlertKey.ALERT_SPLIT_ORDER
}
product_7_dw.setdefault("scenario", scenario1)

product_7_nd = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "alert_type": AlertKey.ALERT_SPLIT_ORDER
}
product_7_nd.setdefault("scenario", scenario1)

product_7_dw_product_amount_2 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 2,
}
product_7_dw_product_amount_2.update(common_test_data.copy())
product_7_dw_product_amount_2.setdefault("scenario", scenario2_amount_2)

product_7_nd_product_amount_2 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 2,
}
product_7_nd_product_amount_2.update(common_test_data.copy())
product_7_nd_product_amount_2.setdefault("scenario", scenario2_amount_2)

product_7_dw_product_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 1
}
product_7_dw_product_amount_1.update(common_test_data.copy())
product_7_dw_product_amount_1.setdefault("scenario", scenario2_amount_1)

product_7_nd_product_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 1
}
product_7_nd_product_amount_1.update(common_test_data.copy())
product_7_nd_product_amount_1.setdefault("scenario", scenario2_amount_1)

product_7_dw_store_gniezno_amount_2 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 2
}
product_7_dw_store_gniezno_amount_2.update(common_test_data.copy())
product_7_dw_store_gniezno_amount_2.setdefault("scenario", scenario3_amount_2)

product_7_nd_store_gniezno_amount_2 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 2
}
product_7_nd_store_gniezno_amount_2.update(common_test_data.copy())
product_7_nd_store_gniezno_amount_2.setdefault("scenario", scenario3_amount_2)

product_7_dw_store_gniezno_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_gniezno"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "product_amount": 1
}
product_7_dw_store_gniezno_amount_1.update(common_test_data.copy())
product_7_dw_store_gniezno_amount_1.setdefault("scenario", scenario3_amount_1)

product_7_nd_store_gniezno_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_gniezno"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "product_amount": 1
}
product_7_nd_store_gniezno_amount_1.update(common_test_data.copy())
product_7_nd_store_gniezno_amount_1.setdefault("scenario", scenario3_amount_1)

product_7_dw_store_poznan_outlet_amount_2 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "product_amount": 2
}
product_7_dw_store_poznan_outlet_amount_2.update(common_test_data.copy())
product_7_dw_store_poznan_outlet_amount_2.setdefault("scenario", scenario3_amount_2)

product_7_nd_store_poznan_outlet_amount_2 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "product_amount": 2
}
product_7_nd_store_poznan_outlet_amount_2.update(common_test_data.copy())
product_7_nd_store_poznan_outlet_amount_2.setdefault("scenario", scenario3_amount_2)

product_7_dw_store_poznan_outlet_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "product_amount": 1
}
product_7_dw_store_poznan_outlet_amount_1.update(common_test_data.copy())
product_7_dw_store_poznan_outlet_amount_1.setdefault("scenario", scenario3_amount_1)

product_7_nd_store_poznan_outlet_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "product_amount": 1
}
product_7_nd_store_poznan_outlet_amount_1.update(common_test_data.copy())
product_7_nd_store_poznan_outlet_amount_1.setdefault("scenario", scenario3_amount_1)

product_7_dw_store_swarzedz_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_swarzedz_partnerski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"]},
    "payment_option": PaymentKey.CASH,
    "product_amount": 1
}
product_7_dw_store_swarzedz_amount_1.update(common_test_data.copy())
product_7_dw_store_swarzedz_amount_1.setdefault("scenario", scenario3_amount_1)

product_7_nd_store_swarzedz_amount_1 = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_swarzedz_partnerski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"]},
    "payment_option": PaymentKey.CASH,
    "product_amount": 1
}
product_7_nd_store_swarzedz_amount_1.update(common_test_data.copy())
product_7_nd_store_swarzedz_amount_1.setdefault("scenario", scenario3_amount_1)

product_7_dw_pickup_gniezno_inpost = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 1
}
product_7_dw_pickup_gniezno_inpost.update(common_test_data.copy())
product_7_dw_pickup_gniezno_inpost.setdefault("scenario", scenario3_amount_1)

product_7_nd_pickup_gniezno_inpost = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 1
}
product_7_nd_pickup_gniezno_inpost.update(common_test_data.copy())
product_7_nd_pickup_gniezno_inpost.setdefault("scenario", scenario3_amount_1)

product_7_dw_pickup_gniezno_dhlpop = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 1
}
product_7_dw_pickup_gniezno_dhlpop.update(common_test_data.copy())
product_7_dw_pickup_gniezno_dhlpop.setdefault("scenario", scenario3_amount_1)

product_7_nd_pickup_gniezno_dhlpop = {
    "product_number": pl_cart_var["product_number_07"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "product_amount": 1
}
product_7_nd_pickup_gniezno_dhlpop.update(common_test_data.copy())
product_7_nd_pickup_gniezno_dhlpop.setdefault("scenario", scenario3_amount_1)
