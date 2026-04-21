from __future__ import annotations

from playwright.sync_api import Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.checkout_overlays import (
    CheckoutPurchaserOverlay,
    DeliveryCourierRecieverOverlay,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.login_overlay import LoginOverlay
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.password_recovery_overlay import (
    PasswordRecoveryOverlay,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.product_page_overlays import (
    ProductPageGoToCartOverlay,
    ProductPagePromotionsOverlay,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.overlays.toast_overlay import ToastOverlay


class Overlays:
    def __init__(self, page: Page):
        self.page = page
        self.__login: LoginOverlay | None = None
        self.__password_recovery: PasswordRecoveryOverlay | None = None
        self.__toast: ToastOverlay | None = None
        self.__go_to_cart: ProductPageGoToCartOverlay | None = None
        self.__promotions: ProductPagePromotionsOverlay | None = None
        self.__checkout_courier_reciever: DeliveryCourierRecieverOverlay | None = None
        self.__checkout_purchaser: CheckoutPurchaserOverlay | None = None

    @property
    def login(self) -> LoginOverlay:
        if self.__login is None:
            self.__login = LoginOverlay(self.page)
        return self.__login

    @property
    def password_recovery(self) -> PasswordRecoveryOverlay:
        if self.__password_recovery is None:
            self.__password_recovery = PasswordRecoveryOverlay(self.page)
        return self.__password_recovery

    @property
    def toast(self) -> ToastOverlay:
        if self.__toast is None:
            self.__toast = ToastOverlay(self.page)
        return self.__toast

    @property
    def go_to_cart(self) -> ProductPageGoToCartOverlay:
        if self.__go_to_cart is None:
            self.__go_to_cart = ProductPageGoToCartOverlay(self.page)
        return self.__go_to_cart

    @property
    def promotions(self) -> ProductPagePromotionsOverlay:
        if self.__promotions is None:
            self.__promotions = ProductPagePromotionsOverlay(self.page)
        return self.__promotions

    @property
    def checkout_courier_reciever(self) -> DeliveryCourierRecieverOverlay:
        if self.__checkout_courier_reciever is None:
            self.__checkout_courier_reciever = DeliveryCourierRecieverOverlay(self.page)
        return self.__checkout_courier_reciever

    @property
    def checkout_purchaser(self) -> CheckoutPurchaserOverlay:
        if self.__checkout_purchaser is None:
            self.__checkout_purchaser = CheckoutPurchaserOverlay(self.page)
        return self.__checkout_purchaser
