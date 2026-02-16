scenario = "Scenariusz: \n" \
           "   1. Wchodzi na stronę produktu z przypisaną etykietą.\n" \
           "   2. Weryfikuje widoczność etykiety w polu pod ceną produktu.\n" \
           "   3. Weryfikuje widoczność etykiety w polu opisowym.\n" \
           "   4. Weryfikuje linkowanie etykiety do zasobu zdalnego.\n"

test_product_labels_with_url = {
    "product_id": 530000001,
    "label_text": "Test Label with url",
    "label_url": "https://www.komputronik.pl/informacje/kontakt/",
}
test_product_labels_with_url.setdefault("scenario", scenario)

test_product_labels_without_url = {
    "product_id": 530000002,
    "label_text": "Test Label without url",
    "label_url": None,
}
test_product_labels_without_url.setdefault("scenario", scenario)

