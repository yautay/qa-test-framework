from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 9.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy pojawił się odpowiedni komunikat.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   4. Sprawdza czy przycisk INPOST, DHL POP, KURIER są niewidoczne.\n" \
            "   5. Sprawdza czy przycisk SALON jest aktywny.\n" \
            "   6. Wraca do koszyka.\n" \
            "   7. Zwiększa ilość do 2 produktów.\n" \
            "   8. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny"

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 9.2, 9.3, 9.4, 9.5, 9.6, 9.7\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy pojawiła się odpowiedni komunikat.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   4. Sprawdza czy przycisk INPOST, DHL POP, KURIER są niewidoczne.\n" \
            "   5. Sprawdza czy przycisk SALON jest aktywny.\n" \
            "   6. Wybiera SALON.\n" \
            "   7. Wyszukuje miasta \"Gniezno\" \"Gdynia\" \"Swarzędz\" i sprawdza czy dla każdego z tych miast nie " \
            "wyświetla się salon.\n" \
            "   8. Wyszukuje miasta \"Warszawa\" i sprawdza czy pojawił się odpowiedni komunikat.\n" \
            "   9. Wybiera Warszawa Megastore i składa zamówienie.\n" \
            "   10. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   11. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
            "oraz czy magazyn to Warszawa Megastore."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_9_dw = {
    "product_number": pl_cart_var["product_number_09"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "methods_allowed": pl_cart_rest_var["storehouses"]}
}
product_9_dw.setdefault("scenario", scenario1)

product_9_nd = {
    "product_number": pl_cart_var["product_number_09"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "methods_allowed": pl_cart_rest_var["storehouses"]}
}
product_9_nd.setdefault("scenario", scenario1)

product_9_dw_pickup_from_store_alocation = {
    "product_number": pl_cart_var["product_number_09"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gniezno"],
                             "delivery_location": pl_cart_var["delivery_location_gniezno"],
                             "object_visibility": False},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gdynia"],
                             "delivery_location": pl_cart_var["delivery_location_gdynia"],
                             "object_visibility": False},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": False}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_9_dw_pickup_from_store_alocation.update(common_test_data.copy())
product_9_dw_pickup_from_store_alocation.setdefault("scenario", scenario2)

product_9_nd_pickup_from_store_alocation = {
    "product_number": pl_cart_var["product_number_09"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gniezno"],
                             "delivery_location": pl_cart_var["delivery_location_gniezno"],
                             "object_visibility": False},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_gdynia"],
                             "delivery_location": pl_cart_var["delivery_location_gdynia"],
                             "object_visibility": False},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": False}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_9_nd_pickup_from_store_alocation.update(common_test_data.copy())
product_9_nd_pickup_from_store_alocation.setdefault("scenario", scenario2)
