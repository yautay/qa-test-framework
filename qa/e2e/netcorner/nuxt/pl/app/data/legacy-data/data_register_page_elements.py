from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData

scenario_register_page_elements = {
        "Scenariusz:\n"
        "   1. Otwiera stronę rejestracji.\n"
        "   2. Sprawdza czy jest widoczny footer i header.\n"
        "   3. Sprawdza czy jest widoczny kontener rejestracji i jego elementy."
}

register_page_elements = {
    "phone_number": PlCommonData.footer_various_elements()["phone_number"],
}

register_page_elements.setdefault("scenario", scenario_register_page_elements)
