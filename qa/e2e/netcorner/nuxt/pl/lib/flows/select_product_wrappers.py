from __future__ import annotations

from contextlib import nullcontext

from playwright.sync_api import BrowserContext, Page

from framework.env import RuntimeEnv
from qa.e2e.conftest import allure
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages import listing_page
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.listing_page import ListingPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.my_account_page import MyAccountPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.register_page import RegisterPage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import ClientData
from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listings_data_models import ListingsData


def _step(title: str):
    if allure is None:
        return nullcontext()
    return allure.step(title)


class SelectProductWrappers:
    def __init__(self, page: Page, context: BrowserContext, runtime_env: RuntimeEnv) -> None:
        self.__page = page
        self.__context = context
        self.__runtime_env = runtime_env

    def select_test_product(self, listings_data: ListingsData | None = None):
        if listings_data:
            with _step(f"Wchodzę na URL kategorii: /{listings_data.category_url}"):
                listing_page = ListingPage(self.__page, f"{self.__runtime_env.base_url}/{listings_data.category_url}")
                listing_page.open().wait_loaded()
            if listings_data.filters:
                listing_page.content.filters.expand_all_filters()
