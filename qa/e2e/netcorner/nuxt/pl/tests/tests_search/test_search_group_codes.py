from __future__ import annotations

import re
import uuid

import allure
import pytest

from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import AdminSearchCodeGroupPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.timeouts import UI_ACTION_MS

pytestmark = [pytest.mark.e2e, pytest.mark.e2e_core, pytest.mark.e2e_search]

_GROUP_CODES = [
    "TEST-FRONT-001---30-CHARACTERS",
    "TEST-FRONT-002",
    "TEST-FRONT-003",
]


@allure.feature("Wyszukiwanie")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.scenario("Admin pozwala utworzyć grupę kodów wyszukiwania, a frontend przyjmuje jej frazę")
def test_search_group_codes(page, runtime_env, admin_panel):
    group_code = f"test_search_codes_group_{uuid.uuid4().hex[:8]}"

    admin_panel.open_admin()
    AdminSearchCodeGroupPage(page, admin_panel.admin_env.base_url).navigate_to_create().create_group(
        code=group_code,
        max_codes=_GROUP_CODES,
    )

    home = HomePage(page, runtime_env.base_url)
    home.open(HomePage.PATH).wait_loaded()
    home.header.search_bar.fill_phrase(group_code)
    home.header.search_bar.submit()
    page.wait_for_url(re.compile(r".*/search/.*"), timeout=UI_ACTION_MS)

    assert f"query={group_code}" in page.url, (
        f"Frontend nie przyjął frazy grupy kodów '{group_code}'. Finalny URL: '{page.url}'."
    )
