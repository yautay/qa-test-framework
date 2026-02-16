from .PlCommonData import PlCommonData

scenario = "Scenariusz: \n" \
           "   1. Otwiera stronę listy produktów, bez wariantów (wyfiltrowane po cenie od 1zł).\n" \
           "   2. Wybiera opcję sortowania.\n" \
           "   3. Sprawdza czy sortowanie jest poprawne." \

pl_var = PlCommonData.variables()

sort_options = {
    "price_ascending": "Po cenie rosnąco",
    "price_descending": "Po cenie malejąco",
    "name_ascending": "Alfabetycznie A-Z",
    "name_descending": "Alfabetycznie Z-A",
}

price_ascending = {
    "sort_type": pl_var["sort_type_price_asc"],
}
price_ascending.setdefault("scenario", scenario)

price_descending = {
    "sort_type": pl_var["sort_type_price_desc"],
}
price_descending.setdefault("scenario", scenario)

name_ascending = {
    "sort_type": pl_var["sort_type_name_asc"],
}
name_ascending.setdefault("scenario", scenario)

name_descending = {
    "sort_type": pl_var["sort_type_name_desc"],
}
name_descending.setdefault("scenario", scenario)
