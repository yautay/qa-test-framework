from __future__ import annotations

import pytest

from qa.e2e.netcorner.nuxt.pl.lib.test_data.register_user_data import valid_client_cases
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
    assert FlowRegisterClient(page, context, runtime_env).register_new_client(user_data), (
        "Użytkownik nie został poprawnie zarejestrowany"
    )
