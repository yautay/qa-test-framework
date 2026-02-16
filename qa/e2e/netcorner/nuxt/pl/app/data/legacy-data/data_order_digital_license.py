import copy

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

scenario_order_registered = "Scenariusz: \n" \
                            "   1.	Otwiera stronę rejestracji, rejestruje klienta. \n" \
                            "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                            " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                            "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'. \n" \
                            "   4. Klika w przycisk 'Realizacja elektroniczna'.  Czeka na proces zakupowy. \n" \
                            "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy. Wypełnia" \
                            " formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki." \
                            " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                            "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                            "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                            "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia - numer" \
                            " oraz cenę.\n"

scenario_order_multiple_registered = "Scenariusz: \n" \
                                     "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                     "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                     " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                     "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej', a następnie" \
                                     " podnosi liczbę sztuk licencji do liczby 2. \n" \
                                     "   4. Klika w przycisk 'Realizacja elektroniczna'. Czeka na proces zakupowy. \n" \
                                     "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy." \
                                     " Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki. " \
                                     "Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                     "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                     "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                     "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                     " - numer oraz cenę.\n"

scenario_order_non_registered = "Scenariusz: \n" \
                                "   1. Otwiera stronę główną. \n" \
                                "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'. \n" \
                                "   4. Klika w przycisk 'Realizacja elektroniczna'. Klika w zamów bez rejestracji" \
                                " i czeka na proces zakupowy. \n" \
                                "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy." \
                                " Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki. " \
                                "Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                " - numer oraz cenę.\n"

scenario_order_multiple_non_registered = "Scenariusz: \n" \
                                         "   1. Otwiera stronę główną. \n" \
                                         "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                         " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                         "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej', a następnie" \
                                         " podnosi liczbę sztuk licencji do liczby 2. \n" \
                                         "   4. Klika w przycisk 'Realizacja elektroniczna'. Klika w zamów bez rejestracji" \
                                         " i czeka na proces zakupowy. \n" \
                                         "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy." \
                                         " Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki. " \
                                         "Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                         "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                         "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                         "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                         " - numer oraz cenę.\n"

scenario_order_with_product_registered = "Scenariusz: \n" \
                                         "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                         "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                         " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                         " drugi produkt z tym samym statusem. \n" \
                                         "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'. \n" \
                                         "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                         "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy." \
                                         " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                         " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                         "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                         "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                         "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                         " - numer oraz cenę.\n"

scenario_order_multiple_with_product_registered = "Scenariusz: \n" \
                                                  "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                                  "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                                  " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                                  " drugi produkt z tym samym statusem. \n" \
                                                  "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej', a następnie podnosi" \
                                                  " liczbę sztuk licencji do liczby 2. \n" \
                                                  "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                                  "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy." \
                                                  " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                                  " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                                  "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                                  "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                                  "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                                  " - numer oraz cenę.\n"

scenario_order_with_product_non_registered = "Scenariusz: \n" \
                                             "   1. Otwiera stronę główną. \n" \
                                             "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                             " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                             " drugi produkt z tym samym statusem. \n" \
                                             "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'. \n" \
                                             "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                             "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy." \
                                             " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                             " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                             "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                             "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                             "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                             " - numer oraz cenę.\n"

scenario_order_multiple_with_product_non_registered = "Scenariusz: \n" \
                                                      "   1. Otwiera stronę główną. \n" \
                                                      "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                                      " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                                      " drugi produkt z tym samym statusem. \n" \
                                                      "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej' a następnie podnosi" \
                                                      " liczbę sztuk licencji do liczby 2. \n" \
                                                      "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                                      "   5. Przełącza na opcję 'Osoba fizyczna' i wypełnia fomularz odbiorcy." \
                                                      " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                                      " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                                      "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                                      "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                                      "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                                      " - numer oraz cenę.\n"

scenario_order_registered_company = "Scenariusz: \n" \
                                    "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                    "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                    " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                    "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'. \n" \
                                    "   4. Klika w przycisk 'Realizacja elektroniczna' i czeka na proces zakupowy. \n" \
                                    "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                    " Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki." \
                                    " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                    "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                    "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                    "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                    " - numer oraz cenę.\n"

scenario_order_multiple_registered_company = "Scenariusz: \n" \
                                             "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                             "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                             " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                             "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej', a następnie podnosi" \
                                             " liczbę sztuk licencji do liczby 2. \n" \
                                             "   4. Klika w przycisk 'Realizacja elektroniczna' i czeka na proces zakupowy. \n" \
                                             "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                             " Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki." \
                                             " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                             "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                             "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                             "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                             " - numer oraz cenę.\n"

scenario_order_non_registered_company = "Scenariusz: \n" \
                                        "   1. Otwiera stronę główną. \n" \
                                        "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                        " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                        "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'. \n" \
                                        "   4. Klika w przycisk 'Realizacja elektroniczna' i czeka na proces zakupowy. \n" \
                                        "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                        " Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki." \
                                        " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                        "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                        "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                        "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                        " - numer oraz cenę.\n"

scenario_order_multiple_non_registered_company = "Scenariusz: \n" \
                                                 "   1. Otwiera stronę główną. \n" \
                                                 "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                                 " Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                                 "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej' a następnie podnosi" \
                                                 " liczbę sztuk licencji do liczby 2. \n" \
                                                 "   4. Klika w przycisk 'Realizacja elektroniczna' i czeka na proces zakupowy. \n" \
                                                 "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                                 " Wypełnia formularz odbiorcy danymi wybiera jedyną dostępną metodę z belki." \
                                                 " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                                 "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                                 "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                                 "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                                 " - numer oraz cenę.\n"

scenario_order_with_product_registered_company = "Scenariusz: \n" \
                                                 "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                                 "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                                 " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                                 " drugi produkt, ze statusem Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                                 "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'. \n" \
                                                 "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                                 "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                                 " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                                 " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                                 "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                                 "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                                 "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                                 " - numer oraz cenę.\n"

scenario_order_multiple_with_product_registered_company = "Scenariusz: \n" \
                                                          "   1. Otwiera stronę rejestracji, rejestruje klienta. \n" \
                                                          "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                                          " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                                          " drugi produkt, ze statusem Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                                          "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej' a następnie podnosi" \
                                                          " liczbę sztuk licencji do liczby 2.\n" \
                                                          "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                                          "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                                          " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                                          " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                                          "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                                          "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                                          "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                                          " - numer oraz cenę.\n"

scenario_order_with_product_non_registered_company = "Scenariusz: \n" \
                                                     "   1. Otwiera stronę główną. \n" \
                                                     "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                                     " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                                     " drugi produkt, ze statusem Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                                     "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej'.\n" \
                                                     "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                                     "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                                     " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                                     " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                                     "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                                     "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                                     "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                                     " - numer oraz cenę.\n"

scenario_order_multiple_with_product_non_registered_company = "Scenariusz: \n" \
                                                              "   1. Otwiera stronę główną. \n" \
                                                              "   2. Wybiera kategorię, wybiera filtry a następnie produkt ze statusem -" \
                                                              " Wysyłamy najczęściej w 1 dzień roboczy. Następnie wybiera kategorię i dobiera" \
                                                              " drugi produkt, ze statusem Wysyłamy najczęściej w 1 dzień roboczy. \n" \
                                                              "   3. Przechodzi do koszyka i klika przycisk 'Przejdź dalej' a następnie" \
                                                              "podnosi liczbę sztuk licencji do liczby 2.\n" \
                                                              "   4. Klika w przycisk 'Zamów z dostawą' i czeka na proces zakupowy. \n" \
                                                              "   5. Przełącza na opcję 'Firma' i wypełnia fomularz odbiorcy." \
                                                              " Wypełnia formularz odbiorcy danymi wybiera pierwszy dostępny dzień z macierzy." \
                                                              " Kopiuje dane do formularza nabywcy i wybiera metodę płatności - Elektroniczna. \n" \
                                                              "   6. Poprawność działania pól w formularzu jest sprawdzana przez asercje.\n" \
                                                              "   7. Składa zamówienie i czeka na pojawienie się thank you page.\n" \
                                                              "   8. Przechodzi do panelu admina i sprawdza poprawność złożonego zamówienia" \
                                                              " - numer oraz cenę.\n"

pl_var = PlCommonData.variables(test_storehouses=True)

common_test_data = {
    "register_data": PlCommonData.register_data(),
    "purchaser_object": {"order_as": PurchaserKey.PRIVATE,
                         "purchaser_data": PlCommonData.purchaser_data_gus()},
    "category": CommonData.url_product_list()["graphic_software"],
    "category_multiple_digital": CommonData.url_product_list()["tools_software"],
    "filters": PlCommonData.filters()[FilterSetKey.DIGITAL_LICENSE],
    "delivery_object": {"order_with": DeliveryMethodKey.DIGITAL,
                        "receiver_data": PlCommonData.receiver_data_ktpl(),
                        "receiver_type": ReceiverKey.PRIVATE},
    "payment_option": PaymentKey.ELECTRONIC_TRANSFER
}
common_with_product_data = {
    "physical_product_category": CommonData.url_product_list()["keyboards"],
    "physical_product_delivery_object": {"order_with": DeliveryMethodKey.COURIER,
                                         "receiver_data": PlCommonData.receiver_data_ktpl(),
                                         "receiver_type": ReceiverKey.PRIVATE},
    "physical_product_payment_option": PaymentKey.ELECTRONIC_TRANSFER
}

order_registered = {
    "order_with_physical_product": False,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_multiple_registered = {
    "order_with_physical_product": False,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_non_registered = {
    "order_with_physical_product": False,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
order_with_product_registered = {
    "order_with_physical_product": True,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_multiple_with_product_registered = {
    "order_with_physical_product": True,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_multiple_non_registered = {
    "order_with_physical_product": False,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
order_with_product_non_registered = {
    "order_with_physical_product": True,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
order_multiple_with_product_non_registered = {
    "order_with_physical_product": True,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
order_registered_company = {
    "order_with_physical_product": False,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_multiple_registered_company = {
    "order_with_physical_product": False,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_non_registered_company = {
    "order_with_physical_product": False,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
order_multiple_non_registered_company = {
    "order_with_physical_product": False,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
order_with_product_registered_company = {
    "order_with_physical_product": True,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_multiple_with_product_registered_company = {
    "order_with_physical_product": True,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
}
order_with_product_non_registered_company = {
    "order_with_physical_product": True,
    "multiple_licences": False,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}
order_multiple_with_product_non_registered_company = {
    "order_with_physical_product": True,
    "multiple_licences": True,
    "order_as": OrderAsKey.ORDER_AS_NON_REGISTERED,
}

order_registered.update(copy.deepcopy(common_test_data))
order_multiple_registered.update(copy.deepcopy(common_test_data))
order_non_registered.update(copy.deepcopy(common_test_data))
order_with_product_registered.update(copy.deepcopy(common_test_data))
order_multiple_with_product_registered.update(copy.deepcopy(common_test_data))
order_multiple_non_registered.update(copy.deepcopy(common_test_data))
order_with_product_non_registered.update(copy.deepcopy(common_test_data))
order_multiple_with_product_non_registered.update(copy.deepcopy(common_test_data))
order_registered_company.update(copy.deepcopy(common_test_data))
order_multiple_registered_company.update(copy.deepcopy(common_test_data))
order_non_registered_company.update(copy.deepcopy(common_test_data))
order_multiple_non_registered_company.update(copy.deepcopy(common_test_data))
order_with_product_registered_company.update(copy.deepcopy(common_test_data))
order_multiple_with_product_registered_company.update(copy.deepcopy(common_test_data))
order_with_product_non_registered_company.update(copy.deepcopy(common_test_data))
order_multiple_with_product_non_registered_company.update(copy.deepcopy(common_test_data))

order_with_product_registered.update(copy.deepcopy(common_with_product_data))
order_multiple_with_product_registered.update(copy.deepcopy(common_with_product_data))
order_with_product_non_registered.update(copy.deepcopy(common_with_product_data))
order_multiple_with_product_non_registered.update(copy.deepcopy(common_with_product_data))
order_with_product_registered_company.update(copy.deepcopy(common_with_product_data))
order_with_product_non_registered_company.update(copy.deepcopy(common_with_product_data))
order_multiple_with_product_non_registered_company.update(copy.deepcopy(common_with_product_data))
order_multiple_with_product_registered_company.update(copy.deepcopy(common_with_product_data))

order_multiple_registered_company["purchaser_object"]["order_as"] = PurchaserKey.COMPANY
order_non_registered_company["purchaser_object"]["order_as"] = PurchaserKey.COMPANY
order_multiple_non_registered_company["purchaser_object"]["order_as"] = PurchaserKey.COMPANY
order_with_product_registered_company["purchaser_object"]["order_as"] = PurchaserKey.COMPANY
order_multiple_with_product_registered_company["purchaser_object"]["order_as"] = PurchaserKey.COMPANY
order_with_product_non_registered_company["purchaser_object"]["order_as"] = PurchaserKey.COMPANY
order_multiple_with_product_non_registered_company["purchaser_object"]["order_as"] = PurchaserKey.COMPANY

order_multiple_registered_company["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_non_registered_company["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_multiple_non_registered_company["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_with_product_registered_company["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_multiple_with_product_registered_company["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_with_product_non_registered_company["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_multiple_with_product_non_registered_company["delivery_object"]["receiver_type"] = ReceiverKey.COMPANY

order_with_product_registered_company["physical_product_delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_with_product_non_registered_company["physical_product_delivery_object"]["receiver_type"] = ReceiverKey.COMPANY
order_multiple_with_product_non_registered_company["physical_product_delivery_object"][
    "receiver_type"] = ReceiverKey.COMPANY

order_registered.setdefault("scenario", scenario_order_registered)
order_multiple_registered.setdefault("scenario", scenario_order_multiple_registered)
order_non_registered.setdefault("scenario", scenario_order_non_registered)
order_multiple_non_registered.setdefault("scenario", scenario_order_multiple_non_registered)
order_with_product_registered.setdefault("scenario", scenario_order_with_product_registered)
order_multiple_with_product_registered.setdefault("scenario", order_multiple_with_product_registered)
order_with_product_non_registered.setdefault("scenario", order_with_product_non_registered)
order_registered_company.setdefault("scenario", order_registered_company)
order_multiple_with_product_non_registered.setdefault("scenario", order_multiple_with_product_non_registered)
order_multiple_registered_company.setdefault("scenario", order_multiple_registered_company)
order_non_registered_company.setdefault("scenario", order_non_registered_company)
order_multiple_non_registered_company.setdefault("scenario", order_multiple_non_registered_company)
order_multiple_with_product_registered_company.setdefault("scenario", order_multiple_with_product_registered_company)
order_with_product_registered_company.setdefault("scenario", order_with_product_registered_company)
order_with_product_non_registered_company.setdefault("scenario", order_with_product_non_registered_company)
order_multiple_with_product_non_registered_company.setdefault("scenario",
                                                              order_multiple_with_product_non_registered_company)
