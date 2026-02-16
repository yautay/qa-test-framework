from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import AlertKey

scenario = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.3 -- A1 - 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, " \
            "1.8, 1.9\"\n" \
            "   1. Otwiera odpowiednie produkty i dodaje je do koszyka.\n" \
            "   2. Sprawdza czy przycisk \"Przejdź dalej\" jest nieaktywny i czy pojawił się odpowiedni alert."

pl_cart_var = PlCommonData.cart_variables(test_storehouses=True)
pl_alerts = PlCommonData.alerts()

product_20 = {
    "product_number": 20,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_20.setdefault("scenario", scenario)

product_21 = {
    "product_number": 21,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_21.setdefault("scenario", scenario)

product_22 = {
    "product_number": 22,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_22.setdefault("scenario", scenario)

product_23 = {
    "product_number": 23,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_23.setdefault("scenario", scenario)

product_24 = {
    "product_number": 24,
    "alert_type": AlertKey.ALERT_COK,
}
product_24.setdefault("scenario", scenario)

product_25 = {
    "product_number": 25,
    "alert_type": AlertKey.ALERT_COK,
}
product_25.setdefault("scenario", scenario)

product_26 = {
    "product_number": 26,
    "alert_type": AlertKey.ALERT_COK,
}
product_26.setdefault("scenario", scenario)

product_27 = {
    "product_number": 27,
    "alert_type": AlertKey.ALERT_COK,
}
product_27.setdefault("scenario", scenario)
