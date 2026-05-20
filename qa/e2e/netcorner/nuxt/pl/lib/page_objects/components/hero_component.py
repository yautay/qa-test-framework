from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


@dataclass(frozen=True)
class OzoDetails:
    """Dane licznika widgetu OZO pobrane ze strony głównej."""

    sold_amount: int
    remaining_amount: int
    days_left: int


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
        self.__daily_deal_widget = self.find("[data-name='DailyDealWidget']")
        self.__daily_deal_name = self.find("[data-name='DailyDealWidgetName']")
        self.__daily_deal_final_price = self.find("[data-name='DailyDealWidgetFinalPrice']")
        self.__deal_progress_bar = self.find("[data-name='dealProgressBar']")

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

    @step("Sprawdzam widoczność widgetu OZO")
    def expect_ozo_widget_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__daily_deal_widget).to_be_visible(timeout=timeout_ms)
        return self

    def is_ozo_widget_present(self, timeout_ms: int = 5_000) -> bool:
        """Return True if the OZO widget is currently visible."""
        return self.__daily_deal_widget.is_visible(timeout=timeout_ms)

    @step("Sprawdzam komplet danych widgetu OZO")
    def expect_ozo_widget_has_core_data(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__daily_deal_name).to_be_visible(timeout=timeout_ms)
        expect(self.__daily_deal_final_price).to_be_visible(timeout=timeout_ms)
        expect(self.__deal_progress_bar).to_be_visible(timeout=timeout_ms)
        return self

    @step("Sprawdzam widoczność poprzedniej ceny w widgetcie OZO")
    def expect_ozo_previous_price_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__daily_deal_widget).to_be_visible(timeout=timeout_ms)
        widget_text = self.__daily_deal_widget.inner_text()
        has_previous_price = bool(re.search(r"Cena bez promocji:\s*\d+", widget_text))
        assert has_previous_price, "Brak poprzedniej ceny ('Cena bez promocji') w widgetcie OZO."
        return self

    @step("Pobieram dane widgetu OZO (sprzedano / pozostało)")
    def get_ozo_details(self, timeout_ms: int = 10_000) -> OzoDetails:
        """Return sold_amount, remaining_amount and days_left from the OZO widget."""
        expect(self.__deal_progress_bar).to_be_visible(timeout=timeout_ms)
        bar_text = self.__deal_progress_bar.inner_text()
        widget_text = self.__daily_deal_widget.inner_text() or ""
        sold_match = re.search(r"Sprzedano[:\s]*(\d+)", bar_text) or re.search(r"Sprzedano[:\s]*(\d+)", widget_text)
        remaining_match = re.search(r"Pozostało[:\s]*(\d+)", bar_text) or re.search(r"Pozostało[:\s]*(\d+)", widget_text)
        days_match = re.search(r"(\d+)\s*dni", widget_text, re.IGNORECASE)
        return OzoDetails(
            sold_amount=int(sold_match.group(1)) if sold_match else 0,
            remaining_amount=int(remaining_match.group(1)) if remaining_match else 0,
            days_left=int(days_match.group(1)) if days_match else -1,
        )

    @step("Klikam w widget OZO (link do produktu)")
    def click_ozo_widget(self) -> None:
        self.pointer_click(self.__daily_deal_widget.locator("a").first)
