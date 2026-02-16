from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData

scenario_cart_verification =              "Scenariusz: \n" \
                                                "   1. Rejestracja klienta.\n" \
                                                "   2. Dodanie produktu do koszyka.\n" \
                                                "   3. Przejście na strone główną.\n" \
                                                "   4. Wylogowanie.\n" \
                                                "   5. Weryfikacja koszyka."

logout_verification_data = {
    "register_data": PlCommonData.register_data(),
    "category": CommonData.url_product_list()["keyboards"]
}
logout_verification_data.setdefault("scenario", scenario_cart_verification)
