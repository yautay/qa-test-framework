from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.PurchaserFactoryLocators import (
    PurchaserFactoryLocators,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.ReceiverFactoryLocators import (
    ReceiverFactoryLocators,
)


class MyAccountLocators:
    BUTTON_logout_user = "//button[contains(text(), 'Wyloguj')]"
    CONTAINER_desktop_account_manager = "//div[@data-name='mainMenuDesktop']"
    BUTTON_manage_purchasers = CONTAINER_desktop_account_manager + "//a[contains(text(), 'Lista danych do faktur')]"
    BUTTON_manage_receivers = CONTAINER_desktop_account_manager + "//a[contains(text(), 'Lista danych do dostawy')]"
    BUTTON_orders_summary = "//div[@data-name='mainMenuDesktop']//*[contains(text(), 'Lista zamówień')]"
    BUTTON_wishlist_summary = "//div[@data-name='mainMenuDesktop']//*[contains(text(), 'Twoje listy życzeń')]"
    ELEMENT_account_login = "//h3//div[contains(text(), 'zalogowany jako')]"


class MyAccountOrdersSummaryLocators:
    BUTTON_order_by_number = "//span[contains(text(), '{order_number}')]/ancestor::div[1]//a/button"
    ELEMENT_order_status = "//div[@data-name='orderStatus']"
    ELEMENT_order_value = "//div[@data-name='orderValue']"


class MyAccountPurchasersManagerLocators(MyAccountLocators, PurchaserFactoryLocators):
    pass


class MyAccountReceiversManagerLocators(MyAccountLocators, ReceiverFactoryLocators):
    pass


class OrderDetailsPageLocators:
    BUTTON_order_cancel = "//button[contains(., 'Anuluj')]"
    TOAST_order_cancel_not_successful_alert = "//li[contains(@data-name, 'toast')]//div[contains(text(), 'nie powiodło')]"
    ELEMENT_order_status = "//div[@data-name='orderStatus']"

class ChangePasswordPageLocators:
    INPUT_old_password = "//input[@id='oldPassword']"
    INPUT_new_password = "//input[@id='newPassword']"
    INPUT_new_password_repeated = "//input[@id='newPasswordRepeated']"
    BUTTON_save_changes = "//button[contains(., 'Zapisz zmiany')]"


class WishlistPageLocators:
    LINK_product_href = "//div[@data-name='cartProductMain']//a"
    BUTTON_create_wishlist = "//button[contains(., 'Utwórz listę')]"
    BUTTON_delete_wishlist_by_name = "//h3[contains(., '{name}')]/ancestor::li//button"
    BUTTON_share_wishlist = "//h3[contains(., '{name}')]/ancestor::li//div[@data-name='shareLinks']"
    ELEMENT_product_box = "//div[@data-name='cardProduct']/div[contains(@class, 'overflow')]"
    BUTTON_add_product_to_cart = "//div[@data-name='cardProduct']//div[contains(@class, 'visible')]//button[contains(., 'Dodaj do koszyka')]"
    BUTTON_delete_product = "//div[@data-product-id='{id}']//div/button"
    TOAST_deleted_product = "//li[@data-name='toast']//div[contains(., 'Usunięto produkt')]"
