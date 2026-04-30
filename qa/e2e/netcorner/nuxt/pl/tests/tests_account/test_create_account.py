from __future__ import annotations

import allure
import pytest

from qa.e2e.netcorner.lib.data_dump_to_logs import dump_data
from qa.e2e.netcorner.nuxt.pl.lib.flows.client_wrappers import ClientWrappers
from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import invalid_client_cases, valid_client_cases

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.account]


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize(
    "user_case",
    valid_client_cases(),
    ids=lambda case: case.case_id,
)
@pytest.mark.scenario("Zakładanie nowego konta")
def test_create_account(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    dump_data(user_case=user_case, user_data=user_data)
    result = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
    assert result, "Użytkownik nie został poprawnie zarejestrowany."


@allure.feature("Konto użytkownika")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.parametrize(
    "user_case",
    invalid_client_cases(),
    ids=lambda case: case.case_id,
)
@pytest.mark.scenario("Nieudane zakładanie konta")
def test_create_account_forbidden(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    dump_data(user_case=user_case, user_data=user_data)
    result = ClientWrappers(page, context, runtime_env).register_new_client(user_data)
    assert not result, "Użytkownik został poprawnie zarejestrowany."
