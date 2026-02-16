class LoginLayerLocators:
    ELEMENT_login_layer_header = "//h2[contains(text(), 'Logowanie')]"
    BUTTON_login = "//button[(contains(., 'Zaloguj')) and not (contains(., 'przez')) and not (contains(., 'Masz')) and not (contains(@class, 'loadingOverlay'))]"
    BUTTON_register = "//a[contains(., 'Załóż konto')]"
    BUTTON_reset_password = "//u[contains(., 'Odzyskaj hasło')]"
    BUTTON_send_password_reset = "//button[contains(., 'Wyślij')]"
    BUTTON_order_without_registration = "//button[contains(., 'Kontynuuj bez logowania')]"
    INPUT_reset_password_email = "//input[@id='resetPasswordEmail']"
    INPUT_login = "//input[@id='loginEmail']"
    INPUT_password = "//input[@id='loginPassword']"


class LayerWithPromotionsLocators:
    ELEMENT_layer_title = "//h2[contains(text(), 'Ten produkt możesz kupić w promocji')]"
    BUTTON_close = ELEMENT_layer_title + "/preceding-sibling::button"
    BUTTON_select_promotion = ELEMENT_layer_title + "/../..//p[contains(text(), '{promotion_title}')]//ancestor::div/button"
    ELEMENT_pagination_promo = ELEMENT_layer_title + "/../..//div[contains(@class, 'pagination-text') and contains(text(), '{promotion_title}')]"


class LayerWithProductRecommendation:
    ELEMENT_layer_title = "//h2[contains(text(), 'Rekomendacja naszych ekspertów')]"
    BUTTON_close = ELEMENT_layer_title + "/preceding-sibling::button"


class CartLayerLocators:
    BUTTON_clean_cart_confirm = "//button[text()='Wyczyść']"


class AfterLoginLayerLocators:
    pass


class LayerWithProductAvailabilityLocators:
    pass


class LayerWithStorehouseAvailabilityLocators:
    CONTAINER_layer = "//h2[contains(text(), 'Dostępność produktu')]"
    BUTTON_show_details = "//button[contains(., 'Pokaż')]"
    CONTAINER_storehouses_list = "//div[@data-name='storehousesList']"
    ELEMENTS_storehouses = CONTAINER_storehouses_list + "/a"


class AfterRegisterLayerLocators:
    pass


class SummaryCartLayerLocators:
    BUTTON_go_to_cart = "//div[contains(@data-variant, 'fullscreen')]//button[contains(., 'Przejdź do koszyka')]"


class OpinionLayerLocators:
    CONTAINER_layer = "//h2[contains(text(), 'Dodawanie opinii o produkcie')]"
    BUTTON_close = CONTAINER_layer + "/preceding-sibling::button"


class LayerProductsAddedToCompareLocators:
    CONTAINER_layer = "//h2[contains(text(), 'Produkty do porównania')]"
    BUTTON_close = CONTAINER_layer + "/preceding-sibling::button"
    BUTTON_compare_now = "//button[contains(., 'Porównaj teraz')]"
    ELEMENT_products_comparison = "//h2[contains(text(), 'Porównanie produktów')]"


class MontageLayerLocators:
    CONTAINER_layer = "//dialog[contains(@class, 'items-center')]"
    BUTTON_apply_changes = CONTAINER_layer + "//div[contains(@class, 'grid gap')]//button[contains(@class, 'end')]"


class LogoutLayerLocators:
    CONTAINER_layer = "//ktr-layer-logout"
    BUTTON_close = CONTAINER_layer + "//button[contains(text(), 'Zamknij')]"


class LayerCompareResultLocators:
    pass


class CookieLayerLocators:
    CONTAINER_cookie_layer = "//div[@id='onetrust-group-container']"
    BUTTON_close_cookie_layer = "//button[@id='onetrust-accept-btn-handler']"
    CONTAINER_cookie_overlay = "//div[contains(@class,'onetrust-pc-dark-filter')]"


class SalesManagoLayerLocators:
    CONTAINER_sales_manago_garbage = "//iframe[@id='bhr-iframe-consent-form']"
    BUTTON_close_garbage_layer = "//button[contains(text(), 'NIE')]"


class CommonReceiverLayerLocators:
    CONTAINER = "//div[@data-name='orderMap']"
    CONTAINER_add_receiver_layer = "//h2[contains(text(), 'dane do')]/ancestor::div[@data-name='OrderAddressDialog']/div"
    BUTTON_close_layer = "//button[contains(., 'Zamknij okno') and contains (@class, 'inline')]"
    ELEMENT_receiver_objects_scroll = "//div[@data-name='parcelList']/parent::div"
    ELEMENT_receiver_objects_tile_by_name = CONTAINER + "//p[contains(text(), '{object_name}')]/ancestor::article[@data-name='orderPickerTile']"
    ELEMENTS_receiver_objects_available = ELEMENT_receiver_objects_scroll + "//article[@data-name='orderPickerTile']//p[contains(@class, 'font-semibold')]"
    BUTTON_confirm_delete_receiver = "//div[@data-variant='modal-base']//button[contains(., 'Usuń')]"
    BUTTON_zoom_out_map = "//a[@title='Zoom out']"
    BUTTON_zoom_in_map = "//a[@title='Zoom in']"
    ELEMENT_zoom_in_request = "//p[contains(text(), 'Powiększ mapę')]"


class NewReceiverCourierLayerLocators(CommonReceiverLayerLocators):
    BUTTON_private_receiver = "//button[contains(., 'Osoba prywatna')]"
    BUTTON_company_receiver = "//button[contains(., 'Firma')]"

    CONTAINER_form = "//form[@data-name='orderFormDialog']"
    INPUT_name = CONTAINER_form + "//input[@id='firstName']"
    INPUT_surname = CONTAINER_form + "//input[@id='surname']"
    INPUT_company = CONTAINER_form + "//input[@id='companyName']"
    INPUT_street = CONTAINER_form + "//input[@id='streetName']"
    INPUT_street_number = CONTAINER_form + "//input[@id='streetNumber']"
    INPUT_post_code = CONTAINER_form + "//input[@id='postalCode']"
    INPUT_phone = CONTAINER_form + "//input[@id='phoneNumber']"
    INPUT_email = CONTAINER_form + "//input[@id='email']"

    DROPDOWN_extend_cities = CONTAINER_form + "//i[contains(@class, 'i-arrow-down')]"
    ELEMENT_city_autofilled = CONTAINER_form + "//div[(contains(., 'Wybierz miejscowość')) and (@data-role='selectLabel')]"
    INPUT_city = CONTAINER_form + "//li[contains(text(), '{city_name}')]"

    BUTTON_add_receiver = CONTAINER_form + "//button[contains(., 'dane')]"
    BUTTON_cancel = CONTAINER_form + "//button[contains(., 'Anuluj')]"

    CONTAINER_delivery_matrix = "//div[@data-name='OrderDeliveryMatrix']"
    ELEMENT_delivery_matrix_item = CONTAINER_delivery_matrix + "//article[@data-name='orderPickerTile']"

    CONTAINER_delivery_list = "//div[@data-name='OrderDeliveryList']"
    ELEMENT_delivery_list_item = CONTAINER_delivery_list + "//article[@data-name='orderPickerTile']"
    ELEMENT_delivery_list_item_name = ELEMENT_delivery_list_item + "//span"

    ELEMENT_delivery_with_lift = "//span[contains(text(), 'Bezpieczne wniesienie')]"

    CHECKBOX_lift_service = "//input[@id='deliveryBringing']"


class NewReceiverStorehouseLayerLocators(CommonReceiverLayerLocators):
    INPUT_postal_code_searchbar = CommonReceiverLayerLocators.CONTAINER + "//input[@id='visitUs']"
    BUTTON_search = CommonReceiverLayerLocators.CONTAINER + "//div[@data-name='searchInput']//button"


class NewReceiverInpostLayerLocators(CommonReceiverLayerLocators):
    INPUT_postal_code = "//span[contains(text(), 'kod')]/ancestor::div[@data-name='searchInput']//input"
    INPUT_box_code = "//span[contains(text(), 'kod paczkomatu')]/ancestor::div[@data-name='searchInput']//input"
    BUTTON_search_postal_code = "//span[contains(text(), 'kod')]/ancestor::div[@data-name='searchInput']//button"
    BUTTON_search_box_code = "//span[contains(text(), 'kod paczkomatu')]/ancestor::div[@data-name='searchInput']//button"


class NewReceiverDhlPopLayerLocators(NewReceiverStorehouseLayerLocators):
    pass


class CommonPurchaserLayerLocators:
    CONTAINER_add_purchaser_layer = "//h2[contains(text(), 'dane do')]/ancestor::div[@data-name='OrderAddressDialog']/div"
    BUTTON_close_layer = "//button[contains(., 'Anuluj')]"
    BUTTON_add_purchaser = "//button[contains(., 'Dodaj dane')]"
    BUTTON_update_purchaser = "//button[contains(., 'Aktualizuj')]"
    BUTTON_private_purchaser = "//button[contains(., 'Osoba prywatna')]"
    BUTTON_company_purchaser = "//button[contains(., 'Firma')]"

    INPUT_postal_code = "//input[@id='postalCode']"
    INPUT_street = "//input[@id='streetName']"
    INPUT_street_number = "//input[@id='streetNumber']"
    INPUT_phone = "//input[@id='phoneNumber']"
    INPUT_email = "//input[@id='email']"

    DROPDOWN_extend_cities = CONTAINER_add_purchaser_layer + "//i[contains(@class, 'i-arrow-down')]"
    SELECT_city = CONTAINER_add_purchaser_layer + "//div[@data-name='selectOptions']/child::div[contains(., '{city_name}')]"
    SELECT_city_empty = CONTAINER_add_purchaser_layer + "//div[@data-role='selectLabel']/child::div"
    INPUT_city = "//input[@id='city']"
    BUTTON_confirm_delete_purchaser = "//div[@data-variant='modal-base']//button[contains(., 'Usuń')]"


class NewPrivatePurchaserLayerLocators(CommonPurchaserLayerLocators):
    INPUT_name = "//input[@id='firstName']"
    INPUT_surname = "//input[@id='surname']"

    CHECKBOX_copy_data_checked = CommonPurchaserLayerLocators.CONTAINER_add_purchaser_layer + "//input[@type='checkbox' and @checked]"
    CHECKBOX_copy_data_unchecked = CommonPurchaserLayerLocators.CONTAINER_add_purchaser_layer + "//input[@type='checkbox']"


class NewCompanyPurchaserLayerLocators(CommonPurchaserLayerLocators):
    INPUT_nip = "//input[@id='taxIdentificationNumber']"
    DROPDOWN_extend_country = "//form[@data-name='orderFormDialog']//div/following-sibling::i"
    SELECT_country = "//div[@data-name='selectOptions']//div[contains(., '{country}')]"
    INPUT_country = "//input[@id='countryName']"
    INPUT_company = "//input[@id='companyName']"


class CommonPurchaserReceiverErrorsLayerLocators:
    @staticmethod
    def forms_error_messages():
        return {
            "name": NewPrivatePurchaserLayerLocators.INPUT_name + "/../span",
            "surname": NewPrivatePurchaserLayerLocators.INPUT_surname + "/../span",
            "street_name": CommonPurchaserLayerLocators.INPUT_street + "/../span",
            "street_number": CommonPurchaserLayerLocators.INPUT_street_number + "/../span",
            "postal_code": CommonPurchaserLayerLocators.INPUT_postal_code + "/../span",
            "city": CommonPurchaserLayerLocators.SELECT_city_empty + "/../../../span",
            "phone": CommonPurchaserLayerLocators.INPUT_phone + "/../span",
            "mail": CommonPurchaserLayerLocators.INPUT_email + "/../span"
        }


class ProductNewsletterLayerLocators:
    ELEMENT_title = "//h2[contains(text(), 'Powiadomienie o dostępności')]"
    INPUT_email = "//input[@id='email']"
    CHECKBOX_terms = "//input[@id='newsletterAgreement']"
    BUTTON_sign_in = "//button[contains(.,'Powiadom mnie o dostępności')]"


class WishlistLayerLocators:
    BUTTON_create_new_wishlist = "//button[contains(text(), 'Utwórz nową listę')]"
    INPUT_wishlist_name = "//input[@id='wishlistInput']"
    BUTTON_create_wishlist = "//div[@data-variant='modal-base']//button[contains(., 'Utwórz listę')]"
    INPUT_wishlist_checkbox = "//input[contains(@id, 'checkboxWishlistAdd')]"
    BUTTON_add_product_to_wishlist = "//button[contains(., 'Dodaj do wybranej')]"
    BUTTON_go_to_wishlist = "//button[contains(., 'Przejdź do listy')]"
    BUTTON_delete_wishlist = "//div[@data-variant='modal-base']//button[contains(., 'Usuń')]"
