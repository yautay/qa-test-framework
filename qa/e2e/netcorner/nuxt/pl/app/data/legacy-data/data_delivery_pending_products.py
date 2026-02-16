from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import DueDeliveryProductKey

pl_var = PlCommonData.variables(test_storehouses=True)
test_products = PlCommonData.due_delivery_products()

scenario = "Scenariusz: \n" \
            "   1. Otwiera odpowiedni produkt z puli produktów testowych. \n" \
            "   2. Na karcie produktu weryfikuje kupowalność"

common_test_data = {
    'scenario': scenario,
}

product_nd_n_due_delivery = {
    'label': 'product_nd_n_due_delivery',
    'product': test_products[DueDeliveryProductKey.ND_N_DUE_DELIVERY]
}
product_dw_n_due_delivery = {
    'label': 'product_dw_n_due_delivery',
    'product': test_products[DueDeliveryProductKey.DW_N_DUE_DELIVERY]
}
product_nda_n_due_delivery = {
    'label': 'product_nda_n_due_delivery',
    'product': test_products[DueDeliveryProductKey.NDA_N_DUE_DELIVERY]
}
product_aka_n_due_delivery = {
    'label': 'product_aka_n_due_delivery',
    'product': test_products[DueDeliveryProductKey.AKA_N_DUE_DELIVERY]
}

product_nd_n_overdue_delivery = {
    'label': 'product_nd_n_overdue_delivery',
    'product': test_products[DueDeliveryProductKey.ND_N_OVERDUE_DELIVERY]
}
product_dw_n_overdue_delivery = {
    'label': 'product_dw_n_overdue_delivery',
    'product': test_products[DueDeliveryProductKey.DW_N_OVERDUE_DELIVERY]
}
product_nda_n_overdue_delivery = {
    'label': 'product_nda_n_overdue_delivery',
    'product': test_products[DueDeliveryProductKey.NDA_N_OVERDUE_DELIVERY]
}
product_aka_n_overdue_delivery = {
    'label': 'product_aka_n_overdue_delivery',
    'product': test_products[DueDeliveryProductKey.AKA_N_OVERDUE_DELIVERY]
}

product_n_due_delivery = {
    'label': 'product_n_due_delivery',
    'product': test_products[DueDeliveryProductKey.N_DUE_DELIVERY]
}
product_n_overdue_delivery = {
    'label': 'product_n_overdue_delivery',
    'product': test_products[DueDeliveryProductKey.N_OVERDUE_DELIVERY]
}

product_nd_n_due_delivery.update(common_test_data.copy())
product_dw_n_due_delivery.update(common_test_data.copy())
product_nda_n_due_delivery.update(common_test_data.copy())
product_aka_n_due_delivery.update(common_test_data.copy())

product_nd_n_overdue_delivery.update(common_test_data.copy())
product_dw_n_overdue_delivery.update(common_test_data.copy())
product_nda_n_overdue_delivery.update(common_test_data.copy())
product_aka_n_overdue_delivery.update(common_test_data.copy())

product_n_due_delivery.update(common_test_data.copy())
product_n_overdue_delivery.update(common_test_data.copy())
