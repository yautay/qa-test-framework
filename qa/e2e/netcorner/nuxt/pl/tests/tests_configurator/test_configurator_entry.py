from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.configurator_page import ConfiguratorPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import AuthSessionCase, ClientDataBuilder, auth_session_cases

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.configurator]


@allure.feature("Konfigurator zestawów")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Wejście w konfigurator zestawów z banera na SG")
def test_configurator_entry_from_banner(page, context, runtime_env, auth_case: AuthSessionCase):
    _test_logic(page, context, runtime_env, auth_case, entry_point="banner")


@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Wejście w konfigurator zestawów z swipe na SG")
def test_configurator_entry_from_swipe(page, context, runtime_env, auth_case: AuthSessionCase):
    _test_logic(page, context, runtime_env, auth_case, entry_point="swiper")

@pytest.mark.parametrize("auth_case", auth_session_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Wejście w konfigurator zestawów z url")
def test_configurator_entry_from_url(page, context, runtime_env, auth_case: AuthSessionCase):
    _test_logic(page, context, runtime_env, auth_case, entry_point="url")


def _prepare_client_session(page, context, runtime_env, auth_case: AuthSessionCase) -> bool:
    if not auth_case.authenticated:
        return False

    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Użytkownik nie został poprawnie zarejestrowany."
    )
    return True

def _test_logic(page, context, runtime_env, auth_case: AuthSessionCase, entry_point: str):
    if not _prepare_client_session(page, context, runtime_env, auth_case):
        HomePage(page, runtime_env.base_url).open().wait_loaded()
    if entry_point == "banner":
        configurator_page = HomePage(page, runtime_env.base_url).open_configurator_from_banner()
    elif entry_point == "swiper":
        configurator_page = HomePage(page, runtime_env.base_url).open_configurator_from_swiper()
    elif entry_point == "url":
        configurator_page = ConfiguratorPage(page, runtime_env.base_url).open(ConfiguratorPage.PATH).wait_loaded()
    else:
        raise ValueError(f"Unsupported configurator entry point: {entry_point}")

    assert configurator_page.content.actions.get_configuration_section_title() != "", \
        "Strona konfiguratora jest niewidoczna!"
