from TestData.CommonData.CommonData import CommonData
from TestData.pl_komputronik_nuxt.PlCommonData import StringGenerator

scenario = "Scenariusz: \n" \
           "   1. Przechodzi na stronę kategorii i wybiera produkt.\n" \
           "   2. Dodaje opinie do produktu. \n" \
           "   3. Przechodzi do admina i akceptuje opinie.\n" \
           "   4. Sprawdza czy opinia wyświetla się na stronie.\n" \
           "   5. Przechodzi do admina i usuwa opinie.\n"

product_opinion = {
    "category": CommonData.url_product_list()["keyboards"],
    "review": f"Opinia testowa, SELENIUM {StringGenerator(10).generated_string}",
}
product_opinion.setdefault("scenario", scenario)
