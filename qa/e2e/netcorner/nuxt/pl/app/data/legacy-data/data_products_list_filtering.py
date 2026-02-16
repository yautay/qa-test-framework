from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import FilterSetKey

scenario = "Scenariusz: \n" \
            "   1. Wchodzi na listę produktów. \n" \
            "   2. Wybiera podane filtry.\n" \
            "   3. Sprawdza czy produkty na liście zawierają podane filtry."

pl_var = PlCommonData.variables()

first_filtering = {
    "category": CommonData.url_product_list()["flash_memory"],
    "filters": PlCommonData.filters()[FilterSetKey.PENDRIVE],
}
first_filtering.setdefault("scenario", scenario)
