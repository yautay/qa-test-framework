from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import AlertKey

scenario = "Scenariusz: \n" \
            "Confluence - \"Ograniczenia koszyka - testy automatyczne cz.3 -- A2 - 1.10, 1.11, 1.12, 1.13, 1.14, " \
            "1.15\"\n" \
            "Scenariusz: \n" \
            "   1. Otwiera odpowiednie produkty i dodaje je do koszyka.\n" \
            "   2. Sprawdza czy przyciski złożenia zamówienia są nieaktywne i czy pojawił się odpowiedni alert."

pl_cart_var_alerts = PlCommonData.alerts()

product_28 = {
    "product_number": 28,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_28.setdefault("scenario", scenario)

product_29 = {
    "product_number": 29,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_29.setdefault("scenario", scenario)

product_30 = {
    "product_number": 30,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_30.setdefault("scenario", scenario)

product_31 = {
    "product_number": 31,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_31.setdefault("scenario", scenario)

product_32 = {
    "product_number": 32,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_32.setdefault("scenario", scenario)

product_33 = {
    "product_number": 33,
    "alert_type": AlertKey.ALERT_SPLIT_ORDER,
}
product_33.setdefault("scenario", scenario)
