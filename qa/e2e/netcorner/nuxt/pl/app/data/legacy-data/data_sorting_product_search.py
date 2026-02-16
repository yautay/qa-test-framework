from .PlCommonData import PlCommonData

scenario = "Scenariusz: \n" \
           "   1. Otwiera stronę główną sklepu i wpisuje nazwę producenta lub produktu w wyszukiwarce.\n" \
           "   2. Wybiera opcję sortowania.\n" \
           "   3. Sprawdza czy sortowanie jest poprawne."

pl_var = PlCommonData.variables()

common_test_data = {
    "search_phrase": pl_var["search_phrase_apple"]
}

price_ascending = {
    "sort_type": pl_var["sort_type_price_asc"],
}
price_ascending.setdefault("scenario", scenario)
price_ascending.update(common_test_data.copy())

price_descending = {
    "sort_type": pl_var["sort_type_price_desc"],
}
price_descending.setdefault("scenario", scenario)
price_descending.update(common_test_data.copy())

name_ascending = {
    "sort_type": pl_var["sort_type_name_asc"],
}
name_ascending.setdefault("scenario", scenario)
name_ascending.update(common_test_data.copy())

name_descending = {
    "search_phrase": pl_var["search_phrase_apple"],
    "sort_type": pl_var["sort_type_name_desc"],
}
name_descending.setdefault("scenario", scenario)
name_descending.update(common_test_data.copy())
