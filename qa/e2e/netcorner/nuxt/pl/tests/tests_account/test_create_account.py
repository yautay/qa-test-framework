from __future__ import annotations

import pytest

from qa.e2e.netcorner.nuxt.pl.lib.test_data.register_user_data import valid_client_cases, invalid_client_cases
from qa.e2e.netcorner.nuxt.pl.lib.wrapers.register_client import FlowRegisterClient
from qa.scenario import scenario

pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.account]


@pytest.mark.parametrize(
    "user_case",
    valid_client_cases(),
    ids=lambda case: case.case_id,
)
@scenario("Account Tests: Zakładanie nowego konta")
def test_create_account(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    result = FlowRegisterClient(page, context, runtime_env).register_new_client(user_data)
    assert result.is_success, f"Użytkownik nie został poprawnie zarejestrowany: {result}"


@pytest.mark.parametrize(
    "user_case",
    invalid_client_cases(),
    ids=lambda case: case.case_id,
)
@scenario("Account Tests: Nieudane zakładanie nowego konta")
def test_create_account_forbidden(page, context, runtime_env, user_case):
    user_data = user_case.factory()
    result = FlowRegisterClient(page, context, runtime_env).register_new_client(user_data)
    assert not result.is_success, f"Użytkownik został poprawnie zarejestrowany: {result}"
