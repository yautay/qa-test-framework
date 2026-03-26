from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.register_user_data import invalid_client_cases, valid_client_cases

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.account]


@allure.feature("Konfigurator zestawów")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize(
    "user_case",
    valid_client_cases(),
    ids=lambda case: case.case_id,
)
@pytest.mark.scenario("Podstawowy proces budowy zestawu")
def test_configurator_basic_flow(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    result = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
    assert result, "Użytkownik nie został poprawnie zarejestrowany."
