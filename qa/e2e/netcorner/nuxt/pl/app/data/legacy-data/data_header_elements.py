from .PlCommonData import PlCommonData

scenario_header_elements = {
    "scenario":
        "Scenariusz:\n"
        "   1. Otwiera stronę główną.\n"
        "   2. Sprawdza czy HEADER ma wszystkie oczekiwane elementy.\n"
        "   3. Sprawdza czy linki mają oczekiwaną wartość atrybutu 'href'.\n"
        "   4. Sprawdza czy nazwy kategorii poziomu zerowego mają oczekiwaną nazwę.\n"
        "   5. Sprawdza czy domyślnie wybrana jest kategoria 'wszędzie'.\n"
}

scenario_search_where_dropdown_menu = {
    "scenario":
        "Scenariusz:\n"
        "   1. Otwiera stronę główną.\n"
        "   2. Sprawdza czy jest widoczny element z menu 'wszędzie'.\n"
        "   3. Klika i sprawdza czy lista zawiera odpowiednie kateogrie.\n"
}

header_elements = {
    "categories_in_header": PlCommonData.variables()["categories_in_header"],
}

search_where_dropdown_menu = {
    "categories_in_header": PlCommonData.variables()["categories_in_header"],
}

header_elements.setdefault("scenario", scenario_header_elements)
search_where_dropdown_menu.setdefault("scenario", scenario_search_where_dropdown_menu)
