from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 9.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Zwiększa ilość do 2 produktów.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny i czy pojawił się odpowiedni alert."

scenario2_with_lift = "Scenariusz: \n" \
                      "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 9.2, 9.3\"\n" \
                      "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                      "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                      "   3. Sprawdza czy przycisk KURIER, SALON są aktywne.\n" \
                      "   4. Klika w KURIER.\n" \
                      "   5. Uzupełnia dane odbiorcy.\n" \
                      "   6. Wybiera dostawę z wniesieniem i składa zamowienie\n" \
                      "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                      "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
                      "oraz czy magazyn to Magazyn Główny."

scenario2_without_lift = "Scenariusz: \n" \
                         "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 9.2, 9.3\"\n" \
                         "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
                         "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
                         "   3. Sprawdza czy przycisk KURIER, SALON są aktywne.\n" \
                         "   4. Klika w KURIER.\n" \
                         "   5. Uzupełnia dane odbiorcy.\n" \
                         "   6. Wybiera dostawę bez wniesienia i składa zamówienie.\n" \
                         "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                         "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
                         "oraz czy magazyn to Magazyn Główny."

scenario3 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.2 -- 9.4, 9.5, 9.6, 9.7, 9.8, 9.9\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Sprawdza czy przycisk KURIER, SALON są aktywne.\n" \
            "   4. Klika w SALON.\n" \
            "   5. Sprawdza czy są niewidoczne salony: Swarzędz, Gdańsk CH Bałtycka.\n" \
            "   6. Wyszukuje miasto i sprawdza czy na pewno nie pojawił się komunikat.\n" \
            "   7. Wybiera punkt odbioru i składa zamówienie.\n" \
            "   8. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   9. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
            "oraz czy magazyn jest poprawny."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_var_real = PlCommonData.cart_variables(test_storehouses=False)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_18_dw = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_DW"]
}
product_18_dw.setdefault("scenario", scenario1)

product_18_nd = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_ND"]
}
product_18_nd.setdefault("scenario", scenario1)

product_18_dw_without_lift_service = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITHOUT_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_18_dw_without_lift_service.update(common_test_data.copy())
product_18_dw_without_lift_service.setdefault("scenario", scenario2_without_lift)

product_18_nd_without_lift_service = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITHOUT_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_18_nd_without_lift_service.update(common_test_data.copy())
product_18_nd_without_lift_service.setdefault("scenario", scenario2_without_lift)

product_18_dw_lift_service = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_18_dw_lift_service.update(common_test_data.copy())
product_18_dw_lift_service.setdefault("scenario", scenario2_with_lift)

product_18_nd_lift_service = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
product_18_nd_lift_service.update(common_test_data.copy())
product_18_nd_lift_service.setdefault("scenario", scenario2_with_lift)

product_18_dw_pickup_poznan_outlet = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gdansk_ch_baltycka"],
                             "delivery_location": pl_cart_var["delivery_location_gdansk"],
                             "object_visibility": None},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": None}
                        ]},
    "payment_option": PaymentKey.CASH
}
product_18_dw_pickup_poznan_outlet.update(common_test_data.copy())
product_18_dw_pickup_poznan_outlet.setdefault("scenario", scenario3)

product_18_nd_pickup_poznan_outlet = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gdansk_ch_baltycka"],
                             "delivery_location": pl_cart_var["delivery_location_gdansk"],
                             "object_visibility": None},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": None}
                        ]},
    "payment_option": PaymentKey.CASH
}
product_18_nd_pickup_poznan_outlet.update(common_test_data.copy())
product_18_nd_pickup_poznan_outlet.setdefault("scenario", scenario3)

product_18_dw_pickup_gdynia = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_gdynia_ch_kwiatkowski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_gdynia"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gdynia"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gdansk_ch_baltycka"],
                             "delivery_location": pl_cart_var["delivery_location_gdansk"],
                             "object_visibility": None},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": None}
                        ]},
    "payment_option": PaymentKey.CASH
}
product_18_dw_pickup_gdynia.update(common_test_data.copy())
product_18_dw_pickup_gdynia.setdefault("scenario", scenario3)

product_18_nd_pickup_gdynia = {
    "product_number": pl_cart_var["product_number_18"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_gdynia_ch_kwiatkowski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_gdynia"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gdynia"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gdansk_ch_baltycka"],
                             "delivery_location": pl_cart_var["delivery_location_gdansk"],
                             "object_visibility": None},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": None}
                        ]},
    "payment_option": PaymentKey.CASH
}
product_18_nd_pickup_gdynia.update(common_test_data.copy())
product_18_nd_pickup_gdynia.setdefault("scenario", scenario3)
