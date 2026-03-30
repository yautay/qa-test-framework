from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.configurator_page import ConfiguratorPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.test_data import ClientDataBuilder, AuthSessionCase, auth_session_not_registered
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import valid_client_cases

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.configurator]


@allure.feature("Konfigurator zestawów")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("auth_case", auth_session_not_registered(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Podstawowy proces budowy zestawu")
def test_configurator_basic_flow(page, context, runtime_env, auth_case: AuthSessionCase):
    if not _prepare_client_session(page, context, runtime_env, auth_case):
        HomePage(page, runtime_env.base_url).open().wait_loaded()
    HomePage(page, runtime_env.base_url).content.hero.go_to_pc_configurator_from_banner()
    ConfiguratorPage(page, runtime_env.base_url).content.components.open_motherboard()
    pass

def _prepare_client_session(page, context, runtime_env, auth_case: AuthSessionCase) -> bool:
    if not auth_case.authenticated:
        return False

    user_data = ClientDataBuilder().with_required_terms().build()
    assert ClientWrappers(page, context, runtime_env).register_new_client(user_data), (
        "Użytkownik nie został poprawnie zarejestrowany."
    )
    return True