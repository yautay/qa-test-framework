from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class HeroComponent(BaseComponent):
    ROOT_SELECTOR = "#pageContent"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Hero Page Root Component")

        # locators (private)
        self.__button_configure_pc = self.find("[data-name='subsidiaryBannerBtn']")
        self.__link_laptops_and_computers = self.find("a[title='Laptopy i komputery']")
        self.__link_pc_configurator = self.find("a[title='Konfigurator PC']")

        self.__image_brand_samsung = self.find("img[data-role='brandLink'][alt='samsung']")
        self.__image_brand_microsoft = self.find("img[data-role='brandLink'][alt='microsoft']")
        self.__image_brand_asus = self.find("img[data-role='brandLink'][alt='asus']")

        self.__section_contact_us = self.find("[data-name='contactUs']")
        self.__section_visit_us = self.find("div:has-text('Odwiedź nas')")

        self.__link_contact_us = self.find("a:has(span:text-is('Skontaktuj się'))")
        self.__link_komputronik_stores = self.find("a:has(span:text-is('Salony Komputronik'))")

        # layout structure locators
        self.__hero_slider = self.find("[data-name='heroSlider']")
        self.__banner_pagination = self.find("#pagination-hero-banner")
        self.__daily_deal = self.find("[data-name='dailyDeal']")

    # actions
    @step("Klikam 'Konfiguruj PC'")
    def go_to_pc_configurator_from_banner(self) -> None:
        self.pointer_click(self.__button_configure_pc)

    @step("Przechodzę do kategorii 'Laptopy i komputery'")
    def go_to_laptops_and_computers(self) -> None:
        self.pointer_click(self.__link_laptops_and_computers)

    @step("Przechodzę do 'Konfigurator PC'")
    def go_to_pc_configurator_from_swiper(self) -> None:
        self.pointer_click(self.__link_pc_configurator)

    @step("Przechodzę do sekcji 'Skontaktuj się'")
    def go_to_contact_us(self) -> None:
        self.pointer_click(self.__link_contact_us)

    @step("Przechodzę do 'Salony Komputronik'")
    def go_to_komputronik_stores(self) -> None:
        self.pointer_click(self.__link_komputronik_stores)

    # assertions
    @step("Sprawdzam widoczność sekcji 'Skontaktuj się z nami'")
    def expect_contact_us_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__section_contact_us).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność sekcji 'Odwiedź nas'")
    def expect_visit_us_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__section_visit_us).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność logo marki Samsung")
    def expect_brand_samsung_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__image_brand_samsung).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność logo marki Microsoft")
    def expect_brand_microsoft_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__image_brand_microsoft).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność logo marki Asus")
    def expect_brand_asus_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__image_brand_asus).to_be_visible(timeout=timeout_ms)
        return self

    # --- layout assertions ---

    @step("Sprawdzam widoczność slidera banerów strony głównej")
    def expect_banners_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__hero_slider).to_be_visible(timeout=timeout_ms)
        expect(self.__banner_pagination).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność sekcji produktów (dailyDeal)")
    def expect_products_section_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__daily_deal).to_be_visible(timeout=timeout_ms)
        return self
