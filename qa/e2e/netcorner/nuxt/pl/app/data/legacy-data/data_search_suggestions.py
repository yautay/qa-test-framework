from .PlCommonData import PlCommonData

scenario = "Scenariusz:\n" \
           "   1. Otwiera stronę główną.\n" \
           "   2. Sprawdza czy jest widoczne pole do wyszukiwania.\n" \
           "   3. Wpisuje podany wyraz i czeka na pojawienie się sugestii.\n" \
           "   4. Sprawdza czy jest widoczna sekcja produktów i ma max. 6 produktów. Sprawdza czy produkty zawierają" \
           " w nazwie podaną frazę.\n" \
           "   5. Sprawdza czy jest widoczna sekcja producenta i czy widoczne jest odpowiednie logo"

pl_var = PlCommonData.variables()

search_samsung = {
    "search_phrase": pl_var["search_suggestions_samsung"],
    "is_producer": True
}
search_samsung.setdefault("scenario", scenario)


search_displays = {
    "search_phrase": pl_var["search_suggestions_displays"],
    "is_producer": False
}
search_displays.setdefault("scenario", scenario)
