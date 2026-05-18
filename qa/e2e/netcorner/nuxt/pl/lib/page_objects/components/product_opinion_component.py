from __future__ import annotations

from playwright.sync_api import Locator, Page, expect

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class ProductOpinionComponent(BaseComponent):
    def __init__(self, scope: Page | Locator) -> None:
        page = scope if isinstance(scope, Page) else scope.page
        form = page.locator("form").filter(has=page.get_by_role("heading", name="Dodaj opinię")).first
        super().__init__(form, name="Product Opinion Component")

        self.__quality_rating = self.find("input[name='quality-rating']")
        self.__functionality_rating = self.find("input[name='functionality-rating']")
        self.__opinion_text = self.find("textarea[name='text']")
        self.__personal_data_agreement = self.find("#personalDataAgreement")
        self.__submit_button = self.root.get_by_role("button", name="Dodaj własną opinię").first

    @step("Oczekuję sekcji dodawania opinii")
    def wait_visible(self, timeout: int = 15_000) -> ProductOpinionComponent:
        expect(self.root).to_be_visible(timeout=timeout)
        return self

    @step("Weryfikuję wymagane pola formularza opinii")
    def has_required_fields(self) -> bool:
        return (
            self.__quality_rating.count() > 0
            and self.__functionality_rating.count() > 0
            and self.__opinion_text.count() > 0
            and self.__personal_data_agreement.count() > 0
            and self.__submit_button.count() > 0
        )
