from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 6.1\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Sprawdza czy przycisk SALON są aktywne.\n" \
            "   4. Powraca z procesu zakupowego do koszyka.\n" \
            "   5. Zwiększa ilość do 2 sztuk i sprawdza czy pojawiły się odpowiednie alerty.\n" \
            "   6. Weryfikuje czy w koszyku nie dodała się druga sztuka produktu.\n" \
            "   7. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   8. Sprawdza czy przycisk SALON są aktywne.\n"

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.1 -- 6.2, 6.3, 6.4, 6.5, 6.6\"\n" \
            "   1. Otwiera odpowiedni produkt i dodaje go do koszyka.\n" \
            "   2. Sprawdza czy przycisk 'Przejdź dalej' jest aktywny i przechodzi dalej.\n" \
            "   3. Sprawdza czy przycisk SALON są aktywne.\n" \
            "   4. Wybiera metodę SALON.\n" \
            "   5. Wpisuje miasto \"Swarzędz\" i sprawdza czy na pewno jest niewidoczne.\n" \
            "   6. Wpisuje miasto \"Poznań\" i sprawdza czy na pewno jest niewidoczne Stary Browar.\n" \
            "   7. Wyszukuje miasta \"Poznań\" i sprawdza czy pojawił się odpowiedni komunikat, " \
            "sprawdza czy jest widoczny tylko Poznań Megastore.\n" \
            "   8. Wybiera punkt odbioru i składa zamówienie.\n" \
            "   9. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   10. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz czy magazyn " \
            "jest poprawny."

pl_var = PlCommonData.variables()
pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_6_dw = {
    "product_number": pl_cart_var["product_number_06"],
    "product_markup": pl_cart_var["product_markup_DW"],
}
product_6_dw.setdefault("scenario", scenario1)

product_6_nd = {
    "product_number": pl_cart_var["product_number_06"],
    "product_markup": pl_cart_var["product_markup_ND"],
}
product_6_nd.setdefault("scenario", scenario1)

product_6_dw_pickup_from_warszawa_megastore = {
    "product_number": pl_cart_var["product_number_06"],
    "product_markup": pl_cart_var["product_markup_DW"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": False},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": False},
                        ]},
    "payment_option": PaymentKey.CASH
}
product_6_dw_pickup_from_warszawa_megastore.update(common_test_data.copy())
product_6_dw_pickup_from_warszawa_megastore.setdefault("scenario", scenario2)

product_6_nd_pickup_from_warszawa_megastore = {
    "product_number": pl_cart_var["product_number_06"],
    "product_markup": pl_cart_var["product_markup_ND"],
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_wawa_megastore"],
                        "methods_allowed": pl_cart_rest_var["storehouses"],
                        "delivery_location": pl_cart_var["delivery_location_warszawa"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_wawa_megastore"],
                        "delivery_object_assertions": [
                            {"delivery_point_name": pl_cart_var["delivery_point_name_poznan_stary_browar"],
                             "delivery_location": pl_cart_var["delivery_location_poznan"],
                             "object_visibility": False},
                            {"delivery_point_name": pl_cart_var["delivery_point_name_swarzedz"],
                             "delivery_location": pl_cart_var["delivery_location_swarzedz"],
                             "object_visibility": False},
                        ]},
    "payment_option": PaymentKey.CASH
}
product_6_nd_pickup_from_warszawa_megastore.update(common_test_data.copy())
product_6_nd_pickup_from_warszawa_megastore.setdefault("scenario", scenario2)
