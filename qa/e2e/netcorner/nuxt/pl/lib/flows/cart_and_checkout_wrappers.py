from __future__ import annotations

from playwright.sync_api import BrowserContext, Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.lib.step_api import step_context
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.components.listing_components import ListingProductData
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listings_data_models import ListingsData


class CartAndCheckoutWrappers:
    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.__page = page
        self.__context = context
        self.__runtime_env = runtime_env

    def process_cart(self) -> ListingProductData | None:
        pass
