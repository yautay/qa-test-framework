from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 3.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy pojawił się odpowiedni komunikat.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   4. Sprawdza czy przycisk INPOST, DHL POP, KURIER są niewidoczne.\n" \
            "   5. Sprawdza czy przycisk SALON jest aktywny.\n" \
            "   6. Wraca do koszyka.\n" \
            "   7. Zwiększa ilość do 2 produktów.\n" \
            "   8. Sprawdza czy przycisk 'Przejdź dalej' jest nieaktywny"

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 3.2, 3.3, 3.4, 3.5, 3.6\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy pojawiła się odpowiedni komunikat.\n" \
            "   3. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   4. Sprawdza czy przycisk INPOST, DHL POP, KURIER są niewidoczne.\n" \
            "   5. Sprawdza czy przycisk SALON jest aktywny.\n" \
            "   6. Wybiera SALON.\n" \
            "   7. Wyszukuje miasta \"Poznań\" \"Warszawa\" i sprawdza czy pojawił się odpowiedni komunikat.\n" \
            "   8. Sprawdza czy nie jest widoczny Stary Browar.\n" \
            "   9. Sprawdza czy jest widoczny Warszawa Megastore."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_var = PlCommonData.variables()
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_3_dw = {
    "product_number": pl_cart_var["product_number_03"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "methods_allowed": pl_cart_rest_var["storehouses"]}
}
product_3_dw.setdefault("scenario", scenario1)

product_3_nd = {
    "product_number": pl_cart_var["product_number_03"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "methods_allowed": pl_cart_rest_var["storehouses"]}
}
product_3_nd.setdefault("scenario", scenario1)

product_3_dw_pickup_from_store_alocation = {
    "product_number": pl_cart_var["product_number_03"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": False}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_3_dw_pickup_from_store_alocation.update(common_test_data.copy())
product_3_dw_pickup_from_store_alocation.setdefault("scenario", scenario2)

product_3_nd_pickup_from_store_alocation = {
    "product_number": pl_cart_var["product_number_03"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": False}]},
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_3_nd_pickup_from_store_alocation.update(common_test_data.copy())
product_3_nd_pickup_from_store_alocation.setdefault("scenario", scenario2)
