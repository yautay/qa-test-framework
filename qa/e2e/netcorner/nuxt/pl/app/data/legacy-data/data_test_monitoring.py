from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_delivery_courier_electronic_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Wysyłka kurierem'. \n" \
                                  "   4. Wypełnia formularz odbiorcy danymi, wybiera pierwszy dostępny dzień" \
                                  " z macierzy. Kopiuje dane do formularza nabywcy i wybiera metodę płatności 'Szybki przelew' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_courier_card = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Wysyłka kurierem'. \n" \
                                  "   4. Wypełnia formularz odbiorcy danymi, wybiera pierwszy dostępny dzień" \
                                  " z macierzy. Kopiuje dane do formularza nabywcy i wybiera metodę płatności 'Karta płatnicza online' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_courier_blik = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Wysyłka kurierem'. \n" \
                                  "   4. Wypełnia formularz odbiorcy danymi, wybiera pierwszy dostępny dzień" \
                                  " z macierzy. Kopiuje dane do formularza nabywcy i wybiera metodę płatności 'BLIK' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_courier_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Wysyłka kurierem'. \n" \
                                  "   4. Wypełnia formularz odbiorcy danymi, wybiera pierwszy dostępny dzień" \
                                  " z macierzy. Kopiuje dane do formularza nabywcy i wybiera metodę płatności 'Przelew - przedpłata' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_inpost_electronic_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Inpost Paczkomat 24/7'. \n" \
                                  "   4. Wybiera paczkomat z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'Szybki przelew' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_inpost_card = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Inpost Paczkomat 24/7'. \n" \
                                  "   4. Wybiera paczkomat z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'Karta płatnicza online' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."


scenario_delivery_inpost_blik = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Inpost Paczkomat 24/7'. \n" \
                                  "   4. Wybiera paczkomat z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'BLIK' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."


scenario_delivery_inpost_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Inpost Paczkomat 24/7'. \n" \
                                  "   4. Wybiera paczkomat z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'Przelew - przedpłata' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."


scenario_delivery_storehouse_electronic_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Salony'. \n" \
                                  "   4. Czeka na proces zakupowy. Wpisuje Poznań w lokalizacje i wybiera salon, " \
                                  "wypełnia formularz nabywcy danymi i wybiera metodę płatności 'Szybki przelew'. \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."


scenario_delivery_storehouse_card = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Salony'. \n" \
                                  "   4. Czeka na proces zakupowy. Wpisuje Poznań w lokalizacje i wybiera salon, " \
                                  "wypełnia formularz nabywcy danymi i wybiera metodę płatności 'Karta płatnicza online'. \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_storehouse_blik = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Salony'. \n" \
                                  "   4. Czeka na proces zakupowy. Wpisuje Poznań w lokalizacje i wybiera salon, " \
                                  "wypełnia formularz nabywcy danymi i wybiera metodę płatności 'BLIK'. \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_storehouse_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Salony'. \n" \
                                  "   4. Czeka na proces zakupowy. Wpisuje Poznań w lokalizacje i wybiera salon, " \
                                  "wypełnia formularz nabywcy danymi i wybiera metodę płatności 'Przelew - przedpłata'. \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_dhlpop_electronic_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'DHL Automaty i punkty'. \n" \
                                  "   4. Wybiera punkty odbioru z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'Szybki przelew' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_dhlpop_card = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'DHL Automaty i punkty'. \n" \
                                  "   4. Wybiera punkty odbioru z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'Karta płatnicza online' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_dhlpop_blik = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'DHL Automaty i punkty'. \n" \
                                  "   4. Wybiera punkty odbioru z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'BLIK' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

scenario_delivery_dhlpop_transfer = "Scenariusz: \n" \
                                  "   1. Przechodzi przez standardową ścieżkę zakupową jako użytkownik niezarejestrowany. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'DHL Automaty i punkty'. \n" \
                                  "   4. Wybiera punkty odbioru z listy i wypełnia formularz nabywcy. Wybiera metodę płatności" \
                                  " 'Przelew - przedpłata' \n" \
                                  "   5. Nie składa zamówienia i nie czeka na pojawienie się thank you page."

pl_var = PlCommonData.variables(test_storehouses=False)
common_var = CommonData()

common_test_data = {
    "category": common_var.url_product_list()["keyboards"],
    "register_data": PlCommonData.register_data(),
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
    "is_logged": False,
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()}

}

delivery_by_courier = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
}

delivery_by_inpost = {
    "delivery_object": {"order_with": DeliveryMethodKey.INPOST,
                        "delivery_location": pl_var["delivery_city_komorniki"],
                        "delivery_point_name": pl_var["delivery_point_inpost"],
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
}

delivery_at_storehouse = {
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "delivery_location": pl_var["delivery_city_komorniki"],
                        "delivery_point_name": pl_var["delivery_point_saloon"],
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
}

delivery_by_dhlpop = {
    "delivery_object": {"order_with": DeliveryMethodKey.DHLPOP,
                        "delivery_location": pl_var["delivery_city_komorniki"],
                        "delivery_point_name": pl_var["delivery_point_dhlps"],
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
}

delivery_courier_electronic_transfer = {
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
delivery_courier_card = {
    "payment_option": PaymentKey.CARD_POLCARD
}
delivery_courier_blik = {
    "payment_option": PaymentKey.BLIK
}
delivery_courier_transfer = {
    "payment_option": PaymentKey.TRANSFER
}

delivery_inpost_electronic_transfer = {
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
delivery_inpost_card = {
    "payment_option": PaymentKey.CARD_POLCARD
}
delivery_inpost_blik = {
    "payment_option": PaymentKey.BLIK
}
delivery_inpost_transfer = {
    "payment_option": PaymentKey.TRANSFER
}

delivery_storehouse_electronic_transfer = {
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
delivery_storehouse_card = {
    "payment_option": PaymentKey.CARD_POLCARD
}
delivery_storehouse_blik = {
    "payment_option": PaymentKey.BLIK
}
delivery_storehouse_transfer = {
    "payment_option": PaymentKey.TRANSFER
}

delivery_dhlpop_electronic_transfer = {
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
delivery_dhlpop_card = {
    "payment_option": PaymentKey.CARD_POLCARD
}
delivery_dhlpop_blik = {
    "payment_option": PaymentKey.BLIK
}
delivery_dhlpop_transfer = {
    "payment_option": PaymentKey.TRANSFER
}

delivery_courier_electronic_transfer.update(common_test_data.copy())
delivery_courier_electronic_transfer.update(delivery_by_courier.copy())
delivery_courier_card.update(common_test_data.copy())
delivery_courier_card.update(delivery_by_courier.copy())
delivery_courier_blik.update(common_test_data.copy())
delivery_courier_blik.update(delivery_by_courier.copy())
delivery_courier_transfer.update(common_test_data.copy())
delivery_courier_transfer.update(delivery_by_courier.copy())

delivery_inpost_electronic_transfer.update(common_test_data.copy())
delivery_inpost_electronic_transfer.update(delivery_by_inpost.copy())
delivery_inpost_card.update(common_test_data.copy())
delivery_inpost_card.update(delivery_by_inpost.copy())
delivery_inpost_blik.update(common_test_data.copy())
delivery_inpost_blik.update(delivery_by_inpost.copy())
delivery_inpost_transfer.update(common_test_data.copy())
delivery_inpost_transfer.update(delivery_by_inpost.copy())

delivery_storehouse_electronic_transfer.update(common_test_data.copy())
delivery_storehouse_electronic_transfer.update(delivery_at_storehouse.copy())
delivery_storehouse_card.update(common_test_data.copy())
delivery_storehouse_card.update(delivery_at_storehouse.copy())
delivery_storehouse_blik.update(common_test_data.copy())
delivery_storehouse_blik.update(delivery_at_storehouse.copy())
delivery_storehouse_transfer.update(common_test_data.copy())
delivery_storehouse_transfer.update(delivery_at_storehouse.copy())

delivery_dhlpop_electronic_transfer.update(common_test_data.copy())
delivery_dhlpop_electronic_transfer.update(delivery_by_dhlpop.copy())
delivery_dhlpop_card.update(common_test_data.copy())
delivery_dhlpop_card.update(delivery_by_dhlpop.copy())
delivery_dhlpop_blik.update(common_test_data.copy())
delivery_dhlpop_blik.update(delivery_by_dhlpop.copy())
delivery_dhlpop_transfer.update(common_test_data.copy())
delivery_dhlpop_transfer.update(delivery_by_dhlpop.copy())

delivery_courier_electronic_transfer.setdefault("scenario", scenario_delivery_courier_electronic_transfer)
delivery_courier_card.setdefault("scenario", scenario_delivery_courier_card)
delivery_courier_blik.setdefault("scenario", scenario_delivery_courier_blik)
delivery_courier_transfer.setdefault("scenario", scenario_delivery_courier_transfer)
delivery_inpost_electronic_transfer.setdefault("scenario", scenario_delivery_inpost_electronic_transfer)
delivery_inpost_card.setdefault("scenario", scenario_delivery_inpost_card)
delivery_inpost_blik.setdefault("scenario", scenario_delivery_inpost_blik)
delivery_inpost_transfer.setdefault("scenario", scenario_delivery_inpost_transfer)
delivery_storehouse_electronic_transfer.setdefault("scenario", scenario_delivery_storehouse_electronic_transfer)
delivery_storehouse_card.setdefault("scenario", scenario_delivery_storehouse_card)
delivery_storehouse_blik.setdefault("scenario", scenario_delivery_storehouse_blik)
delivery_storehouse_transfer.setdefault("scenario", scenario_delivery_storehouse_transfer)
delivery_dhlpop_electronic_transfer.setdefault("scenario", scenario_delivery_dhlpop_electronic_transfer)
delivery_dhlpop_card.setdefault("scenario", scenario_delivery_dhlpop_card)
delivery_dhlpop_blik.setdefault("scenario", scenario_delivery_dhlpop_blik)
delivery_dhlpop_transfer.setdefault("scenario", scenario_delivery_dhlpop_transfer)
