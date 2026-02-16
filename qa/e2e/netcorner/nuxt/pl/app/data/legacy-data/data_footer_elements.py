from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData

scenario_footer_elements = {
        "Scenariusz:\n"
        "   1. Otwiera stronę główną.\n"
        "   2. Sprawdza czy widoczne sa elementy footera.\n"
        "   3. Sprawdza czy widoczna jest sekcja social media i jej elementy.\n"
        "   4. Sprawdza czy widoczna jest sekcja Informacje i jej elementy.\n"
        "   5. Sprawdza czy widoczna jest sekcja Obsługa klienta i jej elementy.\n"
        "   6. Sprawdza czy widoczna jest sekcja Zakupy i jej elementy.\n"
        "   7. Sprawdza czy widoczna jest sekcja Komputronik S.A. i jej elementy.\n"
}

footer_elements = {
    "phone_number": PlCommonData.footer_various_elements()["phone_number"],
    "social_platforms": PlCommonData.footer_various_elements()["social_platforms"],
    "footer_social_section_elements": PlCommonData.footer_social_section_items(),
    "footer_information_elements": PlCommonData.footer_information_elements(),
    "footer_client_service_elements": PlCommonData.footer_client_service_items(),
    "footer_shopping_elements": PlCommonData.footer_shopping_items(),
    "footer_about_us_elements": PlCommonData.footer_about_us_items(),
}

footer_elements.setdefault("scenario", scenario_footer_elements)
