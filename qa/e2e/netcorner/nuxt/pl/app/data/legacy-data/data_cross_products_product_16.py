from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_without_lift = "Scenariusz: \n" \
                        "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.3 -- A3 - 1.17, 1.21, 1.22\"" \
                        "   1. Otwiera odpowiednie produkty i dodaje je do koszyka.\n" \
                        "   2. Dodaje pierwszy produkt i sprawdza czy przycisk \"Przejdź dalej\" jest aktywny," \
                        " nastepnie dla drugiego robi to samo.\n" \
                        "   3. Wybiera KURIER.\n" \
                        "   4. Uzupełnia wszystkie dane, nie zaznacza dostawa z wniesieniem i sprawdza czy na pewno" \
                        " nie pojawila sie macierz, składa zamowienia.\n" \
                        "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                        "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
                        "oraz czy magazyn jest poprawny."

scenario_with_lift = "Scenariusz: \n" \
                     "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.3 -- A3 - 1.17, 1.21, 1.22\"" \
                     "   1. Otwiera odpowiednie produkty i dodaje je do koszyka.\n" \
                     "   2. Dodaje pierwszy produkt i sprawdza czy przycisk \"Przejdź dalej\" jest aktywny, nastepnie" \
                     " dla drugiego robi to samo.\n" \
                     "   3. Wybiera KURIER.\n" \
                     "   4. Uzupełnia wszystkie dane, zaznacza dostawa z wniesieniem i sprawdza czy na pewno nie" \
                     " pojawila sie macierz, składa zamowienia.\n" \
                     "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
                     "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz czy" \
                     " magazyn jest poprawny."

scenario_pickup = "Scenariusz: \n" \
                  "Confluence - \"Ograniczenia koszyka - testy automatyczne " \
                  "cz.3 -- A3 - 1.18, 1.19, 1.20 1.23, 1.24\"\n" \
                  "   1. Otwiera odpowiednie produkty dodaje go do koszyka.\n" \
                  "   2. Dodaje pierwszy produkt i sprawdza czy przycisk \"Przejdź dalej\" jest aktywny, nastepnie" \
                  " dla drugiego robi to samo.\n" \
                  "   3. Sprawdza czy przyciski metod transportu są aktywne.\n" \
                  "   4. Wybiera metodę transportu.\n" \
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

product_35 = {
    "product_number": 35,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_35.update(common_test_data.copy())
product_35.setdefault("scenario", scenario_without_lift)

product_39 = {
    "product_number": 39,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITHOUT_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_39.update(common_test_data.copy())
product_39.setdefault("scenario", scenario_without_lift)

product_40 = {
    "product_number": 40,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_40.update(common_test_data.copy())
product_40.setdefault("scenario", scenario_with_lift)

product_36_pickup_gniezno = {
    "product_number": 36,
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_gniezno"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno"]
                        },
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_36_pickup_gniezno.update(common_test_data.copy())
product_36_pickup_gniezno.setdefault("scenario", scenario_pickup)

product_41_pickup_gdynia = {
    "product_number": 41,
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_gdynia_ch_kwiatkowski"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_gdynia"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gdynia"]
                        },
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_41_pickup_gdynia.update(common_test_data.copy())
product_41_pickup_gdynia.setdefault("scenario", scenario_pickup)

product_42_pickup_poznan_outlet = {
    "product_number": 42,
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"],
                        "delivery_location": pl_cart_var["delivery_location_postal_60001"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_poznan_outlet"]
                        },
    "payment_option": PaymentKey.CARD_POLCARD,
}
product_42_pickup_poznan_outlet.update(common_test_data.copy())
product_42_pickup_poznan_outlet.setdefault("scenario", scenario_pickup)

product_37_pickup_gniezno_inpost = {
    "product_number": 37,
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_inpost"]
                        },
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_37_pickup_gniezno_inpost.update(common_test_data.copy())
product_37_pickup_gniezno_inpost.setdefault("scenario", scenario_pickup)

product_38_pickup_gniezno_dhlpop = {
    "product_number": 38,
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery_inpost_dhlpop"],
                        "delivery_location": pl_cart_var["delivery_location_gniezno"],
                        "delivery_point_name": pl_cart_var["delivery_point_name_gniezno_dhlpop"]
                        },
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_38_pickup_gniezno_dhlpop.update(common_test_data.copy())
product_38_pickup_gniezno_dhlpop.setdefault("scenario", scenario_pickup)
