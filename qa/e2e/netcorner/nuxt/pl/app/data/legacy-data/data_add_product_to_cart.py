from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData

scenario_product_page = "Scenariusz: \n" \
                        "   1. Wybiera produkt testowy.\n" \
                        "   2. Dodaje produkt do koszyka z karty produktu.\n"

scenario_product_form_new_products_box = "Scenariusz: \n" \
                                         "   1. Wybiera produkt z boxów 'NAJNOWSZE PRODUKTY' na stronie głównej. \n" \
                                         "   2. Dodaje produkt do koszyka z karty produktu.\n"

scenario_product_form_recommended_products_box = "Scenariusz: \n" \
                                                 "   1. Wybiera produkt z boxów 'KT POLECA' na stronie głównej. \n" \
                                                 "   2. Dodaje produkt do koszyka z karty produktu.\n"

pl_var = PlCommonData.variables()

product_page_test_data = {
    "category": CommonData.url_product_list()["keyboards"]
}
product_form_new_products_box_test_data = {
}

product_page_test_data.setdefault("scenario", scenario_product_page)
product_form_new_products_box_test_data.setdefault("scenario", scenario_product_form_new_products_box)
