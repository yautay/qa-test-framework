from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.register_page import RegisterPage

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_layout]


@allure.feature("Layout")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Weryfikacja elementów strukturalnych strony rejestracji")
def test_register_page_elements(page, runtime_env):
    """Weryfikuje widoczność kluczowych elementów strony rejestracji:
    - header (nagłówek) i footer (stopka)
    - elementy formularza rejestracji: pola email, hasła, checkboxy regulaminów,
      reCAPTCHA, przyciski "Załóż konto" i "Masz już konto? Zaloguj się."

    Migracja z: LayoutElementsTestsNUXT/TestRegisterPageElements.py
    """
    register = RegisterPage(page, runtime_env.base_url)
    register.open(RegisterPage.PATH)
    register.wait_loaded()

    register.header.assert_visible()
    register.footer.assert_visible()
    register.content.register_form.expect_form_elements_visible()
