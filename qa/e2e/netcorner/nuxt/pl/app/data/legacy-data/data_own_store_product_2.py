from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 2.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Zwiększa ilość do 2 produktów.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny i czy pojawił się odpowiedni alert."

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 2.2\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Wybiera wysyłkę kurierem.\n" \
            "   4. Uzupełnia wszystkie dane i sprawdza czy na pewno nie pojawila sie macierz, składa zamowienia.\n" \
            "   5. Sprawdza czy w szczegółach zamówienia (moje konto) składają się wszystkie dane.\n" \
            "   6. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz czy magazyn" \
            " jest poprawny."

scenario3 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 2.3\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Sprawdza czy przycisk INPOST I DHL POP są niewidoczne.\n" \
            "   4. Wybiera Salony.\n" \
            "   5. Wyszukuje miasta \"Warszawa\" i sprawdza czy pojawił się odpowiedni komunikat.\n" \
            "   6. Sprawdza czy nie jest widoczny Stary Browar.\n" \
            "   7. Sprawdza czy jest widoczny Warszawa Megastore."

scenario4 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 2.4, 2.5, 2.6, 2.7\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Sprawdza czy przycisk INPOST I DHL POP są niewidoczne.\n" \
            "   4. Wpisuje miasto \"Swarzędz\" i sprawdza czy na pewno jest niewidoczne.\n" \
            "   5. Wyszukuje miasta \"Warszawa\" i sprawdza czy pojawił się odpowiedni komunikat.\n" \
            "   6. Wybiera punkt odbioru i składa zamówienie.\n" \
            "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz czy magazyn" \
            " jest poprawny."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_var = PlCommonData.variables()
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_2_dw = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_DW"],
}
product_2_dw.setdefault("scenario", scenario1)

product_2_nd = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_ND"],
}
product_2_nd.setdefault("scenario", scenario1)

product_2_dw_send_from_store = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_2_dw_send_from_store.update(common_test_data.copy())
product_2_dw_send_from_store.setdefault("scenario", scenario2)

product_2_nd_send_from_store = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_2_nd_send_from_store.update(common_test_data.copy())
product_2_nd_send_from_store.setdefault("scenario", scenario2)

product_2_dw_pickup_from_store_alocation = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": True}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_2_dw_pickup_from_store_alocation.update(common_test_data.copy())
product_2_dw_pickup_from_store_alocation.setdefault("scenario", scenario3)

product_2_nd_pickup_from_store_alocation = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": True}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_2_nd_pickup_from_store_alocation.update(common_test_data.copy())
product_2_nd_pickup_from_store_alocation.setdefault("scenario", scenario3)

product_2_dw_pickup_from_warszawa_megastore = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": False}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_2_dw_pickup_from_warszawa_megastore.update(common_test_data.copy())
product_2_dw_pickup_from_warszawa_megastore.setdefault("scenario", scenario4)

product_2_nd_pickup_from_warszawa_megastore = {
    "product_number": pl_cart_var["product_number_02"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": False}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_2_nd_pickup_from_warszawa_megastore.update(common_test_data.copy())
product_2_nd_pickup_from_warszawa_megastore.setdefault("scenario", scenario4)
