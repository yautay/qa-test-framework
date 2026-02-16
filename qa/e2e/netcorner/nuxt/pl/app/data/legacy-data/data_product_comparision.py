from TestData.CommonData.CommonData import CommonData

scenario = "Scenariusz: \n" \
           "   1. Wchodzi na stronę listy produktów bez wariantów (wyfiltrowana po cenie od 1zł).\n" \
           "   2. Dodaje do porównania 3 pierwsze produkty.\n" \
           "   3. Przechodzi do warstwy 'Porównania produktów'.\n" \
           "   4. Sprwadza czy pojawiła się odpowiednia warstwa i oraz czy przycisk 'Pokaż różnice' jest niewidoczny."

product_compare = {
    "scenario": scenario,
    "url": CommonData.url_product_list()["compare_products"]
}
product_compare.setdefault("scenario", scenario)
