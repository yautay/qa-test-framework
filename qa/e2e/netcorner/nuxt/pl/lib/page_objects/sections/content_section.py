from __future__ import annotations

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.cart_components import (
    CartComponent,
    CartSummaryComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.checkout import (
    CheckoutDeliveryMethodsComponent,
    CheckoutDeliveryObjectComponent,
    CheckoutDeliveryTypeComponent,
    CheckoutPaymentMethodsComponent,
    CheckoutPurchaserComponent,
    CheckoutSummaryComponent,
    TypSummaryComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.configurator_components import (
    ConfiguratorActionsComponent,
    ConfiguratorAuxComponentsComponent,
    ConfiguratorComponentsComponent,
    ConfiguratorSummaryComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.content_root_component import ContentRootComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.hero_component import HeroComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import (
    ListingContentComponent,
    ListingFiltersComponent,
    ListingSortingComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.my_account_component import (
    MyAccountComponent,
    MyAccountPasswordChangeComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.password_recovery_component import PasswordRecoveryComponent
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.product_components import (
    ProductActionsComponent,
    ProductPriceComponent,
    ProductRecapComponent,
)
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.register_client_component import RegisterClientComponent


class ContentSection:
    def __init__(self, page: Page):
        self.__content_root = ContentRootComponent(page)

    @property
    def root(self) -> Locator:
        return self.__content_root.root

    def wait_visible(self):
        self.__content_root.wait_visible()
        return self


class PasswordRecoveryContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__password_recovery: PasswordRecoveryComponent | None = None

    @property
    def recovery_form(self) -> PasswordRecoveryComponent:
        if self.__password_recovery is None:
            self.__password_recovery = PasswordRecoveryComponent(self.root)
        return self.__password_recovery


class RegisterContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__register_client: RegisterClientComponent | None = None

    @property
    def register_form(self) -> RegisterClientComponent:
        if self.__register_client is None:
            self.__register_client = RegisterClientComponent(self.root)
        return self.__register_client


class MyAccountContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__my_account: MyAccountComponent | None = None
        self.__my_account_password_change: MyAccountPasswordChangeComponent | None = None

    @property
    def menu_root(self) -> MyAccountComponent:
        if self.__my_account is None:
            self.__my_account = MyAccountComponent(self.root)
        return self.__my_account

    @property
    def menu_change_password(self) -> MyAccountPasswordChangeComponent:
        if self.__my_account_password_change is None:
            self.__my_account_password_change = MyAccountPasswordChangeComponent(self.root)
        return self.__my_account_password_change


class HeroPageContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__hero: HeroComponent | None = None

    @property
    def hero(self) -> HeroComponent:
        if self.__hero is None:
            self.__hero = HeroComponent(self.root)
        return self.__hero


class ConfiguratorContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__set_actions: ConfiguratorActionsComponent | None = None
        self.__components: ConfiguratorComponentsComponent | None = None
        self.__components_aux: ConfiguratorAuxComponentsComponent | None = None
        self.__summary: ConfiguratorSummaryComponent | None = None

    @property
    def actions(self) -> ConfiguratorActionsComponent:
        if self.__set_actions is None:
            self.__set_actions = ConfiguratorActionsComponent(self.root)
        return self.__set_actions

    @property
    def components(self) -> ConfiguratorComponentsComponent:
        if self.__components is None:
            self.__components = ConfiguratorComponentsComponent(self.root)
        return self.__components

    @property
    def aux_components(self) -> ConfiguratorAuxComponentsComponent:
        if self.__components_aux is None:
            self.__components_aux = ConfiguratorAuxComponentsComponent(self.root)
        return self.__components_aux

    @property
    def summary(self) -> ConfiguratorSummaryComponent:
        if self.__summary is None:
            self.__summary = ConfiguratorSummaryComponent(self.root)
        return self.__summary


class ListingContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__filters: ListingFiltersComponent | None = None
        self.__sorting: ListingSortingComponent | None = None
        self.__content: ListingContentComponent | None = None

    @property
    def filters(self) -> ListingFiltersComponent:
        if self.__filters is None:
            self.__filters = ListingFiltersComponent(self.root)
        return self.__filters

    @property
    def sorting(self) -> ListingSortingComponent:
        if self.__sorting is None:
            self.__sorting = ListingSortingComponent(self.root)
        return self.__sorting

    @property
    def content(self) -> ListingContentComponent:
        if self.__content is None:
            self.__content = ListingContentComponent(self.root)
        return self.__content


class ProductContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__recap: ProductRecapComponent | None = None
        self.__price: ProductPriceComponent | None = None
        self.__actions: ProductActionsComponent | None = None

    @property
    def recap(self) -> ProductRecapComponent:
        if self.__recap is None:
            self.__recap = ProductRecapComponent(self.root)
        return self.__recap

    @property
    def price(self) -> ProductPriceComponent:
        if self.__price is None:
            self.__price = ProductPriceComponent(self.root)
        return self.__price

    @property
    def actions(self) -> ProductActionsComponent:
        if self.__actions is None:
            self.__actions = ProductActionsComponent(self.root)
        return self.__actions


class CartContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__cart: CartComponent | None = None
        self.__summary: CartSummaryComponent | None = None

    @property
    def cart(self) -> CartComponent:
        if self.__cart is None:
            self.__cart = CartComponent(self.root)
        return self.__cart

    @property
    def summary(self) -> CartSummaryComponent:
        if self.__summary is None:
            self.__summary = CartSummaryComponent(self.root)
        return self.__summary


class CheckoutContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__delivery_type: CheckoutDeliveryTypeComponent | None = None
        self.__delivery_object: CheckoutDeliveryObjectComponent | None = None
        self.__delivery_methods: CheckoutDeliveryMethodsComponent | None = None
        self.__payment_methods: CheckoutPaymentMethodsComponent | None = None
        self.__purchaser: CheckoutPurchaserComponent | None = None
        self.__summary: CheckoutSummaryComponent | None = None
        self.__typ_summary: TypSummaryComponent | None = None

    @property
    def delivery_type(self) -> CheckoutDeliveryTypeComponent:
        if self.__delivery_type is None:
            self.__delivery_type = CheckoutDeliveryTypeComponent(self.root)
        return self.__delivery_type

    @property
    def delivery_object(self) -> CheckoutDeliveryObjectComponent:
        if self.__delivery_object is None:
            self.__delivery_object = CheckoutDeliveryObjectComponent(self.root)
        return self.__delivery_object

    @property
    def delivery_methods(self) -> CheckoutDeliveryMethodsComponent:
        if self.__delivery_methods is None:
            self.__delivery_methods = CheckoutDeliveryMethodsComponent(self.root)
        return self.__delivery_methods

    @property
    def payment_methods(self) -> CheckoutPaymentMethodsComponent:
        if self.__payment_methods is None:
            self.__payment_methods = CheckoutPaymentMethodsComponent(self.root)
        return self.__payment_methods

    @property
    def purchaser(self) -> CheckoutPurchaserComponent:
        if self.__purchaser is None:
            self.__purchaser = CheckoutPurchaserComponent(self.root)
        return self.__purchaser

    @property
    def summary(self) -> CheckoutSummaryComponent:
        if self.__summary is None:
            self.__summary = CheckoutSummaryComponent(self.root)
        return self.__summary

    @property
    def typ_summary(self) -> TypSummaryComponent:
        if self.__typ_summary is None:
            self.__typ_summary = TypSummaryComponent(self.root)
        return self.__typ_summary
