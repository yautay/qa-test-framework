from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData

scenario_add_product_to_wishlist =              "Scenariusz: \n" \
                                                "   1. Rejestruje klienta.\n" \
                                                "   2. Wchodzi na stronę produktu.\n" \
                                                "   3. Tworzy listę życzeń.\n" \
                                                "   4. Dodaje produkt do listy życzeń.\n" \
                                                "   5. Przechodzi do listy życzeń. \n" \
                                                "   6. Przechodzi na kartę produktu."
scenario_remove_wishlist =                      "Scenariusz: \n" \
                                                "   1. Rejestruje klienta.\n" \
                                                "   2. Wchodzi do list życzeń klienta.\n" \
                                                "   3. Tworzy listę życzeń.\n" \
                                                "   4. Usuwa listę życzeń."
scenario_add_product_to_cart_from_wishlist =    "Scenariusz: \n" \
                                                "   1. Rejestruje klienta.\n" \
                                                "   2. Wchodzi na stronę produktu.\n" \
                                                "   3. Tworzy listę życzeń.\n" \
                                                "   4. Dodaje produkt do listy życzeń.\n" \
                                                "   5. Przechodzi do listy życzeń. \n" \
                                                "   6. Kopiuje share link do listy życzeń. \n" \
                                                "   7. Przechodzi do listy życzeń za pomocą linka. \n" \
                                                "   8. Dodaje produkt do koszyka"
scenario_remove_product_from_wishlist =         "Scenariusz: \n" \
                                                "   1. Rejestruje klienta.\n" \
                                                "   2. Wchodzi na stronę produktu.\n" \
                                                "   3. Tworzy listę życzeń.\n" \
                                                "   4. Dodaje produkt do listy życzeń.\n" \
                                                "   5. Przechodzi do listy życzeń. \n" \
                                                "   6. Usuwa produkt z listy życzeń."

common_test_data = {
    "category": CommonData.url_product_list()["keyboards"],
    "list_name": 'Lista testowa'
}
data_add_product_to_wishlist = {
    "register_data": PlCommonData.register_data()
}
data_remove_wishlist = {
    "register_data": PlCommonData.register_data()
}
data_add_product_to_cart_from_wishlist = {
    "register_data": PlCommonData.register_data()
}
data_remove_product_from_wishlist = {
    "register_data": PlCommonData.register_data()
}

data_add_product_to_wishlist.update(common_test_data.copy())
data_remove_wishlist.update(common_test_data.copy())
data_add_product_to_cart_from_wishlist.update(common_test_data.copy())
data_remove_product_from_wishlist.update(common_test_data.copy())

data_add_product_to_wishlist.setdefault("scenario", scenario_add_product_to_wishlist)
data_remove_wishlist.setdefault("scenario", scenario_remove_wishlist)
data_add_product_to_cart_from_wishlist.setdefault("scenario", scenario_add_product_to_cart_from_wishlist)
data_remove_product_from_wishlist.setdefault("scenario", scenario_remove_product_from_wishlist)
