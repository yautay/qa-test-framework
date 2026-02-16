from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 7.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Zwiększa ilość do 3 produktów.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny i czy pojawił się odpowiedni alert."

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 7.2\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Zwiększa ilość do 2 produktów.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny i czy pojawił się odpowiedni alert."

scenario3_inpost = "Scenariusz: \n" \
                   "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 7.3, 7.4, 7.5, 7.6, 7.7\"\n" \
                   "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                   "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                   "   3. Sprawdza czy przycisk INPOST, DHL POP, KURIER, SALON są aktywne.\n" \
                   "   4. Klika w INPOST.\n" \
                   "   5. Wyszukuje miasto i sprawdza czy na pewno nie pojawił się komunikat.\n" \
                   "   6. Wybiera punkt odbioru i składa zamówienie.\n" \
                   "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                   "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
                   "oraz czy magazyn jest poprawny."

scenario3_dhlpop = "Scenariusz: \n" \
                   "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 7.3, 7.4, 7.5, 7.6, 7.7\"\n" \
                   "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                   "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                   "   3. Sprawdza czy przycisk INPOST, DHL POP, KURIER, SALON są aktywne.\n" \
                   "   4. Klika w DHL POP.\n" \
                   "   5. Wyszukuje miasto i sprawdza czy na pewno nie pojawił się komunikat.\n" \
                   "   6. Wybiera punkt odbioru i składa zamówienie.\n" \
                   "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                   "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
                   "oraz czy magazyn jest poprawny. \n"

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_16_dw = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_DW"]
}
product_16_dw.setdefault("scenario", scenario1)

product_16_nd = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_ND"]
}
product_16_nd.setdefault("scenario", scenario2)

product_16_dw_send_from_warehouse = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_16_dw_send_from_warehouse.update(common_test_data.copy())
product_16_dw_send_from_warehouse.setdefault("scenario", scenario2)

product_16_nd_send_from_warehouse = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_16_nd_send_from_warehouse.update(common_test_data.copy())
product_16_nd_send_from_warehouse.setdefault("scenario", scenario2)

product_16_dw_pickup_stary_browar = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_poznan_stary_browar"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"]},
    "payment_option": PaymentKey.CASH
}
product_16_dw_pickup_stary_browar.update(common_test_data.copy())
product_16_dw_pickup_stary_browar.setdefault("scenario", scenario3_dhlpop)

product_16_nd_pickup_stary_browar = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_poznan_stary_browar"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"]},
    "payment_option": PaymentKey.CASH
}
product_16_nd_pickup_stary_browar.update(common_test_data.copy())
product_16_nd_pickup_stary_browar.setdefault("scenario", scenario3_dhlpop)

product_16_dw_pickup_poznan_outlet = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CASH
}
product_16_dw_pickup_poznan_outlet.update(common_test_data.copy())
product_16_dw_pickup_poznan_outlet.setdefault("scenario", scenario3_dhlpop)

product_16_nd_pickup_poznan_outlet = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CASH
}
product_16_nd_pickup_poznan_outlet.update(common_test_data.copy())
product_16_nd_pickup_poznan_outlet.setdefault("scenario", scenario3_dhlpop)

product_16_dw_pickup_swarzedz = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_swarzedz_partnerski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"]},
    "payment_option": PaymentKey.CASH
}
product_16_dw_pickup_swarzedz.update(common_test_data.copy())
product_16_dw_pickup_swarzedz.setdefault("scenario", scenario3_dhlpop)

product_16_nd_pickup_swarzedz = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_swarzedz_partnerski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"]},
    "payment_option": PaymentKey.CASH
}
product_16_nd_pickup_swarzedz.update(common_test_data.copy())
product_16_nd_pickup_swarzedz.setdefault("scenario", scenario3_inpost)

product_16_dw_pickup_gniezno_inpost = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_16_dw_pickup_gniezno_inpost.update(common_test_data.copy())
product_16_dw_pickup_gniezno_inpost.setdefault("scenario", scenario3_inpost)

product_16_nd_pickup_gniezno_inpost = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_16_nd_pickup_gniezno_inpost.update(common_test_data.copy())
product_16_nd_pickup_gniezno_inpost.setdefault("scenario", scenario3_inpost)

product_16_dw_pickup_gniezno_dhlpop = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_16_dw_pickup_gniezno_dhlpop.update(common_test_data.copy())
product_16_dw_pickup_gniezno_dhlpop.setdefault("scenario", scenario3_dhlpop)

product_16_nd_pickup_gniezno_dhlpop = {
    "product_number": pl_cart_var["product_number_16"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_16_nd_pickup_gniezno_dhlpop.update(common_test_data.copy())
product_16_nd_pickup_gniezno_dhlpop.setdefault("scenario", scenario3_dhlpop)
