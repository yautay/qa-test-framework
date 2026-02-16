from TestData.CommonData.CommonData import CommonData
from TestData.DataProvider import StringGenerator

common_var = CommonData()
temporarily_unavailable_product = {
    "scenario": "Scenariusz: \n" \
                "   1. Wyszukuje produkt tymczasowo niedostępny.\n"
                "   2. Zapisuje urzytkownika do newsleetera.\n"
                "   3. Zmienia zatowarowanie produktu."
                "   3. Weryfikuje mailing newslettera.",
    "category": common_var.url_product_list()["power_adapters"],
    "newsletter": f"test_newsletter_{StringGenerator().generated_string}@tech.nc.pl",
    "assertions": {"from": "Sklep Komputronik.pl",
                   "subject": {"test": "Powiadamianie o dostępności produktu",
                               "demo": "Powiadamianie o dostępności produktu"},
                   "time": "a few seconds ago"},
}
