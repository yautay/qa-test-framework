from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario1 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.3 -- A4 - 1.27, 1.28, 1.29, 1.30\"\n" \
            "   1. Otwiera odpowiednie produkty i dodaje je do koszyka.\n" \
            "   2. Sprawdza czy przyciski \"Przejdź dalej\" jest nieaktywny i czy pojawił się odpowiedni alert."

scenario2 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.3 -- A4 - 1.25, 1.26\"" \
            "   1. Otwiera odpowiednie produkty i dodaje je do koszyka.\n" \
            "   2. Dodaje pierwszy produkt i sprawdza czy przycisk \"Przejdź dalej\" jest aktywny, nastepnie dla" \
            " drugiego robi to samo.\n" \
            "   3. Wybiera KURIER.\n" \
            "   4. Uzupełnia wszystkie dane, nie zaznacza dostawa z wniesieniem i sprawdza czy na pewno nie pojawila" \
            " sie macierz, składa zamowienia.\n" \
            "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane " \
            "oraz czy magazyn jest poprawny."

scenario3 = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.3 -- A4 - 1.25, 1.26\"" \
            "   1. Otwiera odpowiednie produkty i dodaje je do koszyka.\n" \
            "   2. Dodaje pierwszy produkt i sprawdza czy przycisk \"Przejdź dalej\" jest aktywny, nastepnie dla" \
            " drugiego robi to samo.\n" \
            "   3. Wybiera KURIER.\n" \
            "   4. Uzupełnia wszystkie dane, zaznacza dostawa z wniesieniem i sprawdza czy na pewno nie pojawila" \
            " sie macierz, składa zamowienia.\n" \
            "   7. W szczegółach zamówienia sprawdza czy zgadzają się wszystkie dane.\n" \
            "   8. W szczegółach zamówienia w adminie sprawdza czy zgadzają się wszystkie dane oraz czy magazyn" \
            " jest poprawny."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_cart_rest_var = PlCommonData.cart_restrictions_variables()

common_test_data = {
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data()},
}

product_45 = {
    "product_number": 45
}
product_45.setdefault("scenario", scenario1)

product_46 = {
    "product_number": 46
}
product_46.setdefault("scenario", scenario1)

product_47 = {
    "product_number": 47
}
product_47.setdefault("scenario", scenario1)

product_48 = {
    "product_number": 48
}
product_48.setdefault("scenario", scenario1)

product_43_without_lift_service = {
    "product_number": 43,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITHOUT_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_43_without_lift_service.update(common_test_data.copy())
product_43_without_lift_service.setdefault("scenario", scenario2)

product_44_with_lift_service = {
    "product_number": 44,
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER_WITH_LIFT,
                        "receiver_data": PlCommonData.receiver_data(),
                        "receiver_type": ReceiverKey.PRIVATE,
                        "warehouse": pl_cart_var["warehouse_name_magazyn_glowny"],
                        "methods_allowed": pl_cart_rest_var["storehouses_delivery"]},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER,
}
product_44_with_lift_service.update(common_test_data.copy())
product_44_with_lift_service.setdefault("scenario", scenario3)
