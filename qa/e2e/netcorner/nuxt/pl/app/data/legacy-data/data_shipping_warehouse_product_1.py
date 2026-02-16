from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 1.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Zwiększa ilość do 2 produktów.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny i czy pojawił się odpowiedni alert."

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 1.2\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Sprawdza czy przycisk INPOST, DHL POP, KURIER, SALON są aktywne.\n" \
            "   4. Klika w przycisk KURIER.\n" \
            "   5. Uzupełnia wszystkie dane, sprawdza czy lista dostaw jest niewidoczna i składa zamówienie.\n" \
            "   6. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   7. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
            "oraz czy magazyn to Magazyn Główny."

scenario3 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- {confluence}\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Sprawdza czy przycisk INPOST, DHL POP, KURIER, SALON są aktywne.\n" \
            "   6. Wybiera metodę transportu.\n" \
            "   5. Wyszukuje miasto i sprawdza czy na pewno nie pojawił się komunikat.\n" \
            "   6. Wybiera punkt odbioru i składa zamówienie.\n" \
            "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
            "oraz czy magazyn jest poprawny."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_10_dw = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_DW"],
}
product_10_dw.setdefault("scenario", scenario1)

product_10_nd = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_ND"],
}
product_10_nd.setdefault("scenario", scenario1)

product_10_dw_send_from_warehouse = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_10_dw_send_from_warehouse.update(common_test_data.copy())
product_10_dw_send_from_warehouse.setdefault("scenario", scenario2)

product_10_nd_send_from_warehouse = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_10_nd_send_from_warehouse.update(common_test_data.copy())
product_10_nd_send_from_warehouse.setdefault("scenario", scenario2)

product_10_dw_pickup_stary_browar = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_poznan_stary_browar"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "confluence_points": "1.3",
}
product_10_dw_pickup_stary_browar.update(common_test_data.copy())
product_10_dw_pickup_stary_browar.setdefault("scenario", scenario3)

product_10_nd_pickup_stary_browar = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_poznan_stary_browar"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "confluence_points": "1.3",
}
product_10_nd_pickup_stary_browar.update(common_test_data.copy())
product_10_nd_pickup_stary_browar.setdefault("scenario", scenario3)

product_10_dw_pickup_poznan_outlet = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "confluence_points": "1.4",
}
product_10_dw_pickup_poznan_outlet.update(common_test_data.copy())
product_10_dw_pickup_poznan_outlet.setdefault("scenario", scenario3)

product_10_nd_pickup_poznan_outlet = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]},
    "payment_option": PaymentKey.CARD_POLCARD,
    "confluence_points": "1.4",
}
product_10_nd_pickup_poznan_outlet.update(common_test_data.copy())
product_10_nd_pickup_poznan_outlet.setdefault("scenario", scenario3)

product_10_dw_pickup_swarzedz = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_swarzedz_partnerski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"]},
    "payment_option": PaymentKey.CASH,
    "confluence_points": "1.5",
}
product_10_dw_pickup_swarzedz.update(common_test_data.copy())
product_10_dw_pickup_swarzedz.setdefault("scenario", scenario3)

product_10_nd_pickup_swarzedz = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_swarzedz_partnerski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"]},
    "payment_option": PaymentKey.CASH,
    "confluence_points": "1.5",
}
product_10_nd_pickup_swarzedz.update(common_test_data.copy())
product_10_nd_pickup_swarzedz.setdefault("scenario", scenario3)

product_10_dw_pickup_gniezno_inpost = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "confluence_points": "1.6",
}
product_10_dw_pickup_gniezno_inpost.update(common_test_data.copy())
product_10_dw_pickup_gniezno_inpost.setdefault("scenario", scenario3)

product_10_nd_pickup_gniezno_inpost = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_inpost"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "confluence_points": "1.6",
}
product_10_nd_pickup_gniezno_inpost.update(common_test_data.copy())
product_10_nd_pickup_gniezno_inpost.setdefault("scenario", scenario3)

product_10_dw_pickup_gniezno_dhlpop = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "confluence_points": "1.7",
}
product_10_dw_pickup_gniezno_dhlpop.update(common_test_data.copy())
product_10_dw_pickup_gniezno_dhlpop.setdefault("scenario", scenario3)

product_10_nd_pickup_gniezno_dhlpop = {
    "product_number": pl_cart_var["product_number_10"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
    "confluence_points": "1.7",
}
product_10_nd_pickup_gniezno_dhlpop.update(common_test_data.copy())
product_10_nd_pickup_gniezno_dhlpop.setdefault("scenario", scenario3)
