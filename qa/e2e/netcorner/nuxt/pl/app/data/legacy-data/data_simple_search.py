from .PlCommonData import PlCommonData

scenario = "Scenariusz:\n" \
           "   1. Otwiera stronę główną.\n" \
           "   2. Sprawdza czy jest widoczne pole do wyszukiwania.\n" \
           "   3. Wpisuje podany wyraz i czeka na pojawienie się sugestii.\n" \
           "   4. Sprawdza czy jest widoczna sekcja produktów i ma max. 6 produktów. Sprawdza czy produkty zawierają" \
           " w nazwie podaną frazę.\n" \
           "   5. Sprawdza czy jest widoczna sekcja producenta i czy widoczne jest odpowiednie logo"

pl_var = PlCommonData.variables()

search_amd = {
    "search_phrase": pl_var["search_phrase_amd"],
}
search_amd.setdefault("scenario", scenario)

search_ladowarka = {
    "search_phrase": pl_var["search_phrase_charger"],
}
search_ladowarka.setdefault("scenario", scenario)
