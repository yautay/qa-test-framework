from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.PurchaserFactoryLocators import (
    PurchaserFactoryLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.ReceiverFactoryLocators import (
    ReceiverFactoryLocators,
)


class CheckoutLocators(PurchaserFactoryLocators, ReceiverFactoryLocators):
    BUTTON_back_to_cart = "//span[contains(text(), 'Twój koszyk')]"
    CONTAINER_shipping_methods = "//div[@data-name='orderShippingPicker']"
    CONTAINER_receiver_objects_courier = "//div[@data-name='OrderReceiverPicker']"
    CONTAINER_receiver_objects_parcell = "//span[contains(text(), 'odbioru')]/ancestor::section"
    CONTAINER_purchaser_objects = "//div[@data-name='OrderPurchaserPicker']"

    BUTTON_add_purchaser_tile = CONTAINER_purchaser_objects + PurchaserFactoryLocators.BUTTON_add_purchaser_tile
    BUTTON_edit_purchaser_tile_by_name_dropdown = CONTAINER_purchaser_objects + PurchaserFactoryLocators.BUTTON_edit_purchaser_tile_by_name_dropdown
    BUTTON_edit_purchaser_tile_by_name = CONTAINER_purchaser_objects + PurchaserFactoryLocators.BUTTON_edit_purchaser_tile_by_name
    BUTTON_delete_purchaser_tile_by_name = CONTAINER_purchaser_objects + PurchaserFactoryLocators.BUTTON_delete_purchaser_tile_by_name
    ELEMENTS_purchaser_tiles = CONTAINER_purchaser_objects + PurchaserFactoryLocators.ELEMENTS_purchaser_tiles

    BUTTON_checkout_delivery = CONTAINER_shipping_methods + "//p[contains(text(), 'kurier')]/ancestor::article"
    BUTTON_checkout_storehouse = CONTAINER_shipping_methods + "//p[contains(text(), 'Salony')]/ancestor::article"
    BUTTON_checkout_digital = CONTAINER_shipping_methods + "//p[contains(text(), 'elektroniczna')]/ancestor::article"
    BUTTON_checkout_dhlpop = CONTAINER_shipping_methods + "//p[contains(text(), 'DHL')]/ancestor::article"
    BUTTON_checkout_inpost = CONTAINER_shipping_methods + "//p[contains(text(), 'InPost')]/ancestor::article"

    CHECKBOX_electronic_invoice = "//input[@id='electronicInvoice']"
    CONTAINER_payment = "//div[@data-name='orderPaymentPicker']"
    ELEMENT_payment_tile_by_name = CONTAINER_payment + "//p[contains(text(), '{payment}')]/ancestor::article"
    CHECKBOX_add_comment = "//input[@id='orderUserCommentCheckbox']"
    INPUT_comments = "//textarea[@id='orderUserCommentTextarea']"
    CHECKBOX_terms = "//input[@id='regulation']"
    CHECKBOX_terms_outlet = "//input[@id='outletTerms']"
    CHECKBOX_terms_digital = "//input[@id='electronicLicenceTerms']"
    CHECKBOX_mca_license_digital = "//input[@id='molpCspTerms']"
    BUTTON_submit_order = "//section[@data-name='orderSummaryCheckout']//button"
    ELEMENT_alert = "//p[contains(text(), '{alert_msg}')]"


class OrderDetailsThankYouPageLocators:
    ELEMENT_order_number = "//p[contains(.,'Numer zamówienia')]/following-sibling::p"
    ELEMENT_order_shipping_value = "//span[contains(.,'Dostawa')]/following-sibling::span"
    ELEMENT_order_value = "//p[contains(.,'Do zapłaty')]/following-sibling::span"
