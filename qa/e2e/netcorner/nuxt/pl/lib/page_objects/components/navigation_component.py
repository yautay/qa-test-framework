from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class NavigationComponent(BaseComponent):
    ROOT_SELECTOR = '[data-name="navigationBar"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Navigation Component")

        self.__categories_bar = self.find("[data-name='megamenuDesktop'][data-categories-lvl='0']")

    # --- layout assertions ---

    @step("Sprawdzam widoczność paska kategorii poziomu 0")
    def expect_categories_bar_visible(self, timeout_ms: int = 10_000) -> Self:
        expect(self.__categories_bar).to_be_visible(timeout=timeout_ms)
        return self

    @step("Pobieram liczbę kategorii poziomu 0")
    def get_zero_level_category_count(self) -> int:
        return self.__categories_bar.locator("li").count()

    # --- megamenu traversal ---

    def __get_root_category_li(self, root_name: str) -> Locator:
        """Returns the root <li> element for the given root category name."""
        return self.__categories_bar.locator("li").filter(has_text=root_name).first

    def __find_level1_index(self, dropdown: Locator, level1_name: str) -> int:
        """Returns the 0-based index of the level-1 category matching level1_name, or -1."""
        items = dropdown.locator("ul[data-categories-lvl='1'] li a")
        count = items.count()
        for i in range(count):
            text = (items.nth(i).text_content() or "").strip()
            if level1_name.lower() in text.lower():
                return i
        return -1

    @step("Pobieram linki poziomu 2 megamenu dla: {root_name} > {level1_name}")
    def get_level2_links_for(self, root_name: str, level1_name: str) -> list[str]:
        """Returns all level-2 category hrefs visible in the megamenu panel
        when root_name root category is open and level1_name item is selected.

        Reads directly from the DOM (bypassing display:none) — equivalent to
        what the Selenium hover-based implementation collected.
        """
        root_li = self.__get_root_category_li(root_name)
        dropdown = root_li.locator("[data-role='dropdownContent']")
        idx = self.__find_level1_index(dropdown, level1_name)
        if idx < 0:
            return []
        level2_div = dropdown.locator("div[data-categories-lvl='2']").nth(idx)
        hrefs: list[str | None] = level2_div.evaluate(
            "el => [...el.querySelectorAll('a')].map(a => a.getAttribute('href'))"
        )
        return [h for h in hrefs if h]

    @step("Pobieram linki poziomu 2 (tekst+href) megamenu dla: {root_name} > {level1_name}")
    def get_level2_items_for(self, root_name: str, level1_name: str) -> list[tuple[str, str]]:
        """Returns (link_text, href) pairs for all level-2 links in the panel for level1_name.

        Use this instead of get_level2_links_for when you need to look up links by
        visible text (e.g. category name) rather than URL fragment — required for
        categories whose slugs do not contain the Polish display name.
        """
        root_li = self.__get_root_category_li(root_name)
        dropdown = root_li.locator("[data-role='dropdownContent']")
        idx = self.__find_level1_index(dropdown, level1_name)
        if idx < 0:
            return []
        level2_div = dropdown.locator("div[data-categories-lvl='2']").nth(idx)
        raw: list[list[str]] = level2_div.evaluate(
            "el => [...el.querySelectorAll('a')].map(a => [a.textContent.trim(), a.getAttribute('href') || ''])"
        )
        return [(text, href) for text, href in raw if href]

    @step("Pobieram href kategorii poziomu 1: {root_name} > {level1_name}")
    def get_level1_href(self, root_name: str, level1_name: str) -> str:
        """Returns the href of the level-1 category link matching level1_name."""
        root_li = self.__get_root_category_li(root_name)
        dropdown = root_li.locator("[data-role='dropdownContent']")
        items = dropdown.locator("ul[data-categories-lvl='1'] li a")
        count = items.count()
        for i in range(count):
            item = items.nth(i)
            text = (item.text_content() or "").strip()
            if level1_name.lower() in text.lower():
                return item.get_attribute("href") or ""
        return ""


class CheckoutNavigationComponent(BaseComponent):
    ROOT_SELECTOR = '[data-role="order-stepper"]'

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Cart Navigation Component")

        self.__back_to_shopping_link = self.find("a:has-text('Wróć do zakupów')")
        self.__step_1 = self.find("[data-step='1']")
        self.__step_2 = self.find("[data-step='2']")
        self.__step_3 = self.find("[data-step='3']")
        self.__step_4 = self.find("[data-step='4']")

    def __get_step_locator(self, step: int) -> Locator:
        if step == 1:
            return self.__step_1
        if step == 2:
            return self.__step_2
        if step == 3:
            return self.__step_3
        if step == 4:
            return self.__step_4
        raise ValueError(f"Unsupported step: {step}")

    def __click_step(self, step: int) -> None:
        step_locator = self.__get_step_locator(step).first
        if step_locator.count() == 0 or not step_locator.is_visible():
            raise AssertionError(f"Step {step} is not visible")

        tag_name = (step_locator.evaluate("el => el.tagName") or "").lower()
        if tag_name != "a":
            raise AssertionError(f"Step {step} is not clickable in current state")

        self.pointer_click(step_locator)

    @step("Klikam 'Wróć do zakupów'")
    def click_back_to_shopping(self) -> None:
        self.pointer_click(self.__back_to_shopping_link)

    @step("Klikam krok 1")
    def click_step_1(self) -> None:
        self.__click_step(1)

    @step("Klikam krok 2")
    def click_step_2(self) -> None:
        self.__click_step(2)

    @step("Klikam krok 3")
    def click_step_3(self) -> None:
        self.__click_step(3)

    @step("Klikam krok 4")
    def click_step_4(self) -> None:
        self.__click_step(4)

    @step("Pobieram bieżący krok zamówienia")
    def get_current_step(self) -> int:
        raw = (self.root.get_attribute("data-current-step") or "").strip()
        try:
            return int(raw)
        except ValueError:
            return 0
