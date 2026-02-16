from TestData.pl_komputronik_nuxt.PlCommonData import CommonData, PlCommonData

scenario_password_recovery =              "Scenariusz: \n" \
                                                "   1. Rejestracja klienta.\n" \
                                                "   2. Wylogowanie klienta.\n" \
                                                "   3. Odzyskanie hasła.\n" \
                                                "   4. Zdobycie linka z maila.\n" \
                                                "   5. Zmiana hasła.\n" \
                                                "   6. Zalogowanie nowymi danymi."

password_recovery_data = {
    "register_data": PlCommonData.register_data(),
    "new_password": 'passwordtest123',
    "category": CommonData.url_product_list()["keyboards"],
}
password_recovery_data.setdefault("scenario", scenario_password_recovery)
