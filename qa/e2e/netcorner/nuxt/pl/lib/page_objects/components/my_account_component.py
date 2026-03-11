from __future__ import annotations

from playwright.sync_api import Locator, expect

from qa.e2e.netcorner.nuxt.pl.lib.allure_decorators import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class MyAccountComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="My Account Root Component")

        self.__logged_as_text = self.find("text=Jesteś zalogowany jako:")
        self.__logout = self.find('div.cursor-pointer.underline:has-text("(wyloguj)")')

        self.__wishlist = self.find('a[href="/customer/account/wishlist"]')
        self.__personal_data = self.find('a[href="/customer/account/personal"]')
        self.__password_change = self.find('a[href="/customer/account/password-change"]')
        self.__customer_consents = self.find('a[href="/customer/account/customer-consents"]')
        self.__purchasers = self.find('a[href="/customer/account/purchasers"]')
        self.__receivers = self.find('a[href="/customer/account/receivers"]')

        self.__orders = self.find('a[href="/customer/account/orders"]')
        self.__bought_products = self.find('a[href="/customer/account/bought-products"]')
        self.__invoices = self.find('a[href="/customer/account/invoices"]')
        self.__shared_cart = self.find('a[href="/customer/account/shared-cart"]')
        self.__complaints = self.find('a[href="/informacje/pomoc/reklamacje"]')

    @step("Odczytuję kto jest zalogowany w panelu klienta")
    def get_logged_as(self) -> str:
        text = self.__logged_as_text.text_content() or ""
        return text.split(":", 1)[-1].strip()

    @step("Klikam link 'Wyloguj' w panelu konta")
    def logout(self) -> None:
        self.safe_click(self.__logout)

    @step("Otwieram listę życzeń")
    def open_wishlist(self) -> None:
        self.safe_click(self.__wishlist)

    @step("Przechodzę do danych osobowych klienta")
    def open_personal_data(self) -> None:
        self.safe_click(self.__personal_data)

    @step("Przechodzę do zmiany hasła")
    def open_password_change(self) -> None:
        self.safe_click(self.__password_change.first)

    @step("Otwieram zakładkę zgód klienta")
    def open_consents(self) -> None:
        self.safe_click(self.__customer_consents)

    @step("Przechodzę do listy nabywców")
    def open_purchasers(self) -> None:
        self.safe_click(self.__purchasers)

    @step("Przechodzę do odbiorców")
    def open_receivers(self) -> None:
        self.safe_click(self.__receivers)

    @step("Otwieram listę zamówień klienta")
    def open_orders(self) -> None:
        self.safe_click(self.__orders)

    @step("Przechodzę do zakupionych produktów")
    def open_bought_products(self) -> None:
        self.safe_click(self.__bought_products)

    @step("Oczekuję na faktury klienta")
    def open_invoices(self) -> None:
        self.safe_click(self.__invoices)

    @step("Otwieram wspólny koszyk")
    def open_shared_cart(self) -> None:
        self.safe_click(self.__shared_cart)

    @step("Przechodzę do zgłoszeń reklamacyjnych")
    def open_complaints(self) -> None:
        self.safe_click(self.__complaints)


class MyAccountPasswordChangeComponent(BaseComponent):
    def __init__(self, root: Locator) -> None:
        super().__init__(root, name="My Account Password Change Component")

        self.__breadcrumb_account = self.find('a[href="/customer/account"]')
        self.__input_old_password = self.find("#oldPassword")
        self.__input_new_password = self.find("#newPassword")
        self.__input_new_password_repeated = self.find("#newPasswordRepeated")
        self.__button_save = self.find('button:has-text("Zapisz zmiany")')

    def __fill_old_password(self, password: str) -> MyAccountPasswordChangeComponent:
        self.safe_type(self.__input_old_password, password)
        return self

    def __fill_new_password(self, password: str) -> MyAccountPasswordChangeComponent:
        self.safe_type(self.__input_new_password, password)
        return self

    def __fill_new_password_repeated(self, password: str) -> MyAccountPasswordChangeComponent:
        self.safe_type(self.__input_new_password_repeated, password)
        return self

    def __submit(self) -> None:
        self.safe_click(self.__button_save)

    @step("Wracam do głównej sekcji konta")
    def back_to_account(self) -> None:
        self.safe_click(self.__breadcrumb_account)

    @step("Zmiana hasła z {old_pwd} na {new_pwd}")
    def change_password(self, old_pwd: str, new_pwd: str) -> None:
        self.__fill_old_password(old_pwd).__fill_new_password(new_pwd).__fill_new_password_repeated(new_pwd).__submit()
