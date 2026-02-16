from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import FilterSetKey

scenario = "Scenariusz: \n" \
                "   1. Wchodzi na listę produktów. \n" \
                "   2. Wybiera filtr przypisany do produktów z przekreśloną ceną."
pl_var = PlCommonData.variables()

data_sezam_filtering = {
    "scenario": scenario,
    "category": CommonData.url_product_list()["laptops_casual"],
    "filters": PlCommonData.filters()[FilterSetKey.REDUCED_PRICE],
}
