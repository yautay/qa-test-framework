from .PlCommonData import PlCommonData

scenario = "Scenariusz: \n" \
           "   1. Wchodzi do admina do modułu tworzenia agregatora.\n" \
           "   2. Wypełnia formularz danymi agregatora.\n" \
           "   3. Tworzy nowy element agregatora i wypełnia formularz danymi. \n" \
           "   3. Loguje się na konto.\n" \
           "   4. Sprawdza czy jest widoczny agregator." \


aggregator_category = {
    "aggregator_data": PlCommonData.aggregator_data_category(),
    "aggregator_element_data": PlCommonData.aggregator_category_element_data()
}

aggregator_products = {
    "aggregator_data": PlCommonData.aggregator_data_products(),
    "aggregator_element_data": PlCommonData.aggregator_products_element_data()
}

aggregator_category.setdefault("scenario", scenario)
aggregator_products.setdefault("scenario", scenario)
