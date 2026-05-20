from __future__ import annotations

import time
from typing import Callable, TypeVar

from playwright.sync_api import Page

_T = TypeVar("_T")


def poll_until(
    fn: Callable[[], _T],
    *,
    condition: Callable[[_T], bool],
    timeout_s: float,
    poll_s: float,
    default: _T,
) -> _T:
    """Wywołuje fn() w pętli aż condition(wynik) == True lub upłynie timeout_s.

    Zwraca ostatnią wartość zwróconą przez fn() (asercja należy do testu).
    Używa time.sleep między próbami — przeznaczony do polling zasobów backendowych
    (API, strona, widget), nie do oczekiwania na elementy Playwright (tam używaj expect).

    Parametry:
        fn         – callable bez argumentów, wywoływany przy każdej próbie
        condition  – predykat na wyniku fn(); jeśli True, polling kończy się natychmiast
        timeout_s  – maksymalny łączny czas oczekiwania w sekundach
        poll_s     – przerwa między próbami w sekundach
        default    – wartość zwracana gdy fn() nie zostało jeszcze wywołane (nie powinno wystąpić)
    """
    deadline = time.monotonic() + timeout_s
    last: _T = default
    while time.monotonic() <= deadline:
        last = fn()
        if condition(last):
            return last
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(poll_s, remaining))
    return last

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.cart_page import CartPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.product_page import ProductPage


def accept_cookie_banner_if_visible(page: Page) -> None:
    button = page.locator("#onetrust-accept-btn-handler")
    if button.count() == 0 or not button.first.is_visible():
        return
    button.first.click(force=True)
    page.wait_for_timeout(1_000)


def open_home_and_accept_cookies(page: Page, base_url: str) -> None:
    HomePage(page, base_url).open().wait_loaded()
    accept_cookie_banner_if_visible(page)


def open_product_page(page: Page, base_url: str, product_path: str) -> ProductPage:
    page.goto(f"{base_url}{product_path}", wait_until="domcontentloaded")
    accept_cookie_banner_if_visible(page)
    return ProductPage(page, base_url).wait_loaded()


def add_products_to_cart_from_paths(page: Page, base_url: str, product_paths: list[str]) -> CartPage:
    if not product_paths:
        raise ValueError("Lista product_paths nie może być pusta.")

    for index, product_path in enumerate(product_paths):
        product_page = open_product_page(page, base_url, product_path)
        product_page.add_to_cart()
        page.wait_for_timeout(1_000)
        accept_cookie_banner_if_visible(page)

        promo_button = page.get_by_role("button", name="Nie, dziękuję - chcę kupić tylko produkt")
        if promo_button.count() and promo_button.first.is_visible():
            promo_button.first.click(force=True)
            page.wait_for_timeout(500)

        next_button_name = "Przejdź do koszyka" if index == len(product_paths) - 1 else "Wróć do zakupów"
        next_button = page.get_by_role("button", name=next_button_name)
        if next_button.count() and next_button.first.is_visible():
            next_button.first.click(force=True)
            page.wait_for_timeout(500)
            if index == len(product_paths) - 1:
                return CartPage(page, base_url).wait_loaded()
        if index < len(product_paths) - 1:
            continue

    page.goto(f"{base_url}/cart", wait_until="domcontentloaded")
    return CartPage(page, base_url).wait_loaded()
