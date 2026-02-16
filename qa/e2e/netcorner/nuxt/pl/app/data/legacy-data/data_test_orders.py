from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import (
    DeliveryMethodKey,
    FilterSetKey,
    OrderAsKey,
    PaymentKey,
    PurchaserKey,
    ReceiverKey,
)

scenario_self_pickup_registered = "Scenariusz: \n" \
                                  "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Zamów z odbiorem osobistym'. " \
                                  "   4. Czeka na proces zakupowy. Wpisuje Poznań w lokalizacje i wybiera salon, " \
                                  "wypełnia formularz nabywcy danymi i wybiera metodę płatności." \
                                  "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_self_pickup_logged_in_cart = "Scenariusz: \n" \
                                      "   1. Otwiera stronę rejestracji, rejestruje klienta, wylogowuje go.\n" \
                                      "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka " \
                                      "pierwszy dostępny produkt na magazynie 3210. \n" \
                                      "   3. Klika w przycisk 'Zamów z odbiorem osobistym'. Loguje się w koszyku" \
                                      " i czeka na proces zakupowy. \n" \
                                      "   4. Wpisuje Poznań w lokalizacje i wybiera salon, wypełnia formularz nabywcy "\
                                      "danymi i wybiera metodę płatności." \
                                      "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_self_pickup_non_registered = "Scenariusz: \n" \
                                      "   1. Otwiera stronę rejestracji, nie rejestruje klienta. \n" \
                                      "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka " \
                                      "pierwszy dostępny produkt na magazynie 3210. \n" \
                                      "   3. Klika w przycisk 'Zamów z dostawą'. Nie loguje się w koszyku i " \
                                      "czeka na proces zakupowy. \n" \
                                      "4.  Wpisuje Poznań w lokalizacje i wybiera salon, wypełnia formularz nabywcy" \
                                      " danymi i wybiera metodę płatności." \
                                      "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_delivery_home_registered = "Scenariusz: \n" \
                                  "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Zamów z dostawą'. Czeka na proces zakupowy. \n" \
                                  "   4. Wypełnia formularz odbiorcy danymi, wybiera pierwszy dostępny dzień" \
                                  " z macierzy. Kopiuje dane do formularza nabywcy i wybiera metodę płatności" \
                                  "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_delivery_home_logged_in_cart = "Scenariusz: \n" \
                                        "   1. Otwiera stronę rejestracji, rejestruje klienta, wylogowuje go.\n" \
                                        "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka " \
                                        "pierwszy dostępny produkt na magazynie 3210. \n" \
                                        "   3. Klika w przycisk 'Zamów z dostawą'. Loguje się w koszyku i czeka na" \
                                        " proces zakupowy. \n" \
                                        "   4. Wypełnia formularz odbiorcy danymi, Wpisuje Poznań w lokalizacje " \
                                        "i wybiera salon w Poznaniu, wypełnia formularz nabywcy i wybiera " \
                                        "metodę płatności. \n" \
                                        "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_delivery_home_non_registered = "Scenariusz: \n" \
                                        "   1. Otwiera stronę rejestracji, nie rejestruje klienta. \n" \
                                        "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka " \
                                        "pierwszy dostępny produkt na magazynie 3210. \n" \
                                        "   3. Klika w przycisk 'Zamów z dostawą'. Nie loguje się w koszyku i " \
                                        "czeka na proces zakupowy. \n" \
                                        "   4. Wypełnia formularz odbiorcy danymi, Wpisuje Познань w lokalizacje " \
                                        "i wybiera salon w Poznaniu, wypełnia formularz nabywcy i wybiera " \
                                        "metodę płatności. \n" \
                                        "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_digital_registered = "Scenariusz: \n" \
                              "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                              "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                              "dostępny produkt na magazynie 3210. \n" \
                              "   3. Klika w przycisk 'Realizacja elektroniczna'. Wypełnia formularz odbiorcy danymi " \
                              "wybiera jedyną dostępną metodę z belki. " \
                              "   4. Kopiuje dane do formularza nabywcy i wybiera metodę płatności." \
                              "   5. Składa zamówienie i czeka na pojawienie się thank you page." \

scenario_digital_logged_in_cart = "Scenariusz: \n" \
                                  "   1. Otwiera stronę rejestracji, rejestruje klienta, wylogowuje go. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Realizacja elektroniczna'. Loguje się w koszyku i " \
                                  "czeka na proces zakupowy " \
                                  "   4. Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki. " \
                                  "Kopiuje dane do formularza nabywcy i wybiera metodę płatności." \
                                  "   5. Składa zamówienie i czeka na pojawienie się thank you page." \

scenario_digital_non_registered = "Scenariusz: \n" \
                                  "   1. Otwiera stronę rejestracji, nie rejestruje klienta. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka " \
                                  "pierwszy dostępny produkt na magazynie 3210. \n" \
                                  "   3. Klika w przycisk 'Realizacja elektroniczna'. Nie loguje się w koszyku i " \
                                  "czeka na proces zakupowy. \n" \
                                  "   4. Wypełnia formularz odbiorcy danymi, wybiera jedyną dostępną metodę z belki. " \
                                  "Kopiuje dane do formularza nabywcy i wybiera metodę płatności." \
                                  "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_digital_with_product_non_registered = "Scenariusz: \n" \
                                  "   1. Otwiera stronę rejestracji, nie rejestruje klienta. \n" \
                                  "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                                  "dostępny produkt ze statusem 'Wysyłka natychmiastowa'. Zmienia kategorię i dodaje " \
                                  "dodatkowy produkt dostępny na magazynie 3210. \n" \
                                  "   3. Nie loguje się w koszyku i czeka na proces zakupowy. \n" \
                                  "   4. Wypełnia formularz odbiorcy danymi, wybiera dostępną metodę z belki. " \
                                  "Kopiuje dane do formularza nabywcy i wybiera metodę płatności." \
                                  "   5. Składa zamówienie i czeka na pojawienie się thank you page."

scenario_digital_with_product_registered = "Scenariusz: \n" \
                              "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                              "   2. Przechodzi na listę produktów w kategorii i dodaje do koszyka pierwszy " \
                              "dostępny produkt ze statusem 'Wysyłka natychmiastowa'. Zmienia kategorię i dodaje " \
                              "dodatkowy produkt dostępny na magazynie 3210. \n" \
                              "   3. Wypełnia formularz odbiorcy danymi i wybiera dostępną metodę z belki. " \
                              "   4. Kopiuje dane do formularza nabywcy i wybiera metodę płatności." \
                              "   5. Składa zamówienie i czeka na pojawienie się thank you page." \

pl_var = PlCommonData.variables(test_storehouses=True)
common_var = CommonData()

common_test_data = {
    "category": common_var.url_product_list()["keyboards"],
    "register_data": PlCommonData.register_data(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_ktpl()}

}

delivery_home_data = {
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}

self_pickup_data = {
    "delivery_object": {"order_with": DeliveryMethodKey.STOREHOUSE,
                        "delivery_location": pl_var["delivery_city_poznan"],
                        "delivery_point_name": pl_var["delivery_point_saloon"]},
    "payment_option": PaymentKey.CASH
}

digital_data = {
    "category": common_var.url_product_list()["graphic_software"],
    "filters": PlCommonData.filters()[FilterSetKey.DIGITAL_LICENSE],
    "delivery_object": {"order_with": DeliveryMethodKey.DIGITAL,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}

mixed_products_data = {
    "category": [common_var.url_product_list()["graphic_software"], common_var.url_product_list()["keyboards"]],
    "filters": [PlCommonData.filters()[FilterSetKey.DIGITAL_LICENSE], None],
    "delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE
                        },
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}

delivery_at_home_registered = {
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
delivery_at_home_logged_in_cart = {
    "order_as": OrderAsKey.ORDER_AS_LOGGED_IN_CART,
}
delivery_at_home_non_registered = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED
}
self_pickup_registered = {
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
self_pickup_logged_in_cart = {
    "order_as": OrderAsKey.ORDER_AS_LOGGED_IN_CART,
}
self_pickup_non_registered = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}


digital_licence_registered = {
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
digital_licence_non_registered = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
mixed_licence_with_product_registered = {
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
mixed_licence_with_product_non_registered = {
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}

delivery_at_home_registered.update(common_test_data.copy())
delivery_at_home_registered.update(delivery_home_data.copy())

delivery_at_home_logged_in_cart.update(common_test_data.copy())
delivery_at_home_logged_in_cart.update(delivery_home_data.copy())

delivery_at_home_non_registered.update(common_test_data.copy())
delivery_at_home_non_registered.update(delivery_home_data.copy())

self_pickup_registered.update(common_test_data.copy())
self_pickup_registered.update(self_pickup_data.copy())

self_pickup_logged_in_cart.update(common_test_data.copy())
self_pickup_logged_in_cart.update(self_pickup_data.copy())

self_pickup_non_registered.update(common_test_data.copy())
self_pickup_non_registered.update(self_pickup_data.copy())

digital_licence_registered.update(common_test_data.copy())
digital_licence_registered.update(digital_data.copy())

digital_licence_non_registered.update(common_test_data.copy())
digital_licence_non_registered.update(digital_data.copy())

mixed_licence_with_product_registered.update(common_test_data.copy())
mixed_licence_with_product_registered.update(mixed_products_data.copy())

mixed_licence_with_product_non_registered.update(common_test_data.copy())
mixed_licence_with_product_non_registered.update(mixed_products_data.copy())

delivery_at_home_registered.setdefault("scenario", scenario_delivery_home_registered)
delivery_at_home_logged_in_cart.setdefault("scenario", scenario_delivery_home_logged_in_cart)
delivery_at_home_non_registered.setdefault("scenario", scenario_delivery_home_non_registered)
self_pickup_registered.setdefault("scenario", scenario_self_pickup_registered)
self_pickup_logged_in_cart.setdefault("scenario", scenario_self_pickup_logged_in_cart)
self_pickup_non_registered.setdefault("scenario", scenario_self_pickup_non_registered)
digital_licence_registered.setdefault("scenario", scenario_digital_registered)
digital_licence_non_registered.setdefault("scenario", scenario_digital_non_registered)
mixed_licence_with_product_registered.setdefault("scenario", scenario_digital_with_product_registered)
mixed_licence_with_product_non_registered.setdefault("scenario", scenario_digital_with_product_non_registered)
