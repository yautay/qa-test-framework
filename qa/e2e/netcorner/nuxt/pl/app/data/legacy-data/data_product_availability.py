from TestData.pl_komputronik_nuxt.PlCommonKeys import ProductAvailabilityKey

scenario = "Scenariusz: \n" \
           "   1. Wchodzi na stronę produktu.\n" \
           "   2. Weryfikuje status dostępności.\n" \
           "   3. Weryfikuje dostępność na widoku zatowarowania w salonach."

data_product_availability_last_item = {
    "scenario": scenario,
    "product_id": 3600001,
    "product_page_status": ProductAvailabilityKey.AVAILABLE_IN_SELECTED_STORES.value,
    "storehouses_availability": [ProductAvailabilityKey.AVAILABLE_LAST_ITEM.value]

}
data_product_availability_large_qty = {
    "scenario": scenario,
    "product_id": 500000501,
    "product_page_status": ProductAvailabilityKey.AVAILABLE.value,
    "storehouses_availability": [ProductAvailabilityKey.AVAILABLE_IN_HQ.value, ProductAvailabilityKey.LARGE_QTY.value]
}
