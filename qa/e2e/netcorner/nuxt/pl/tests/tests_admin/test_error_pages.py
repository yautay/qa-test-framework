from __future__ import annotations

from urllib.parse import quote

import allure
import pytest
import requests

from qa.e2e.netcorner.admin.lib.page_objects.pages.admin_delta_pages import AdminMissingLinksPage

pytestmark = [pytest.mark.e2e]

_ERROR_404_PATHS = [
    "adasdasdasd",
    "product/982",
]

_ERROR_410_PATHS = [
    "product/982201/zegarek-smartwatch-polar-",
    "product/982201/",
    "search/category/5022?query=laptopy",
]


def _request_status(base_url: str, path: str) -> int:
    response = requests.get(f"{base_url.rstrip('/')}/{path.lstrip('/')}", verify=False, timeout=20)
    return response.status_code


def _missing_link_is_logged(page, admin_panel, link: str) -> bool:
    filter_value = quote(f"*{link}*", safe="")
    admin_panel.navigate_to(f"missingLink/list/pl?filters[missing_link_url]={filter_value}&filter=filtruj")
    return AdminMissingLinksPage(page, admin_panel.admin_env.base_url).wait_loaded().has_link_entry(link)


@allure.feature("Admin")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("path", _ERROR_410_PATHS, ids=lambda path: path.replace("/", "_"))
@pytest.mark.scenario("Strony oznaczone historycznie jako 410 odpowiadają kodem 200 na aktualnym env")
def test_error_pages_410(runtime_env, path: str):
    status_code = _request_status(runtime_env.base_url, path)
    assert status_code == 200, f"Dla ścieżki '{path}' oczekiwano kodu 200, znaleziono {status_code}."


@allure.feature("Admin")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("path", _ERROR_404_PATHS, ids=lambda path: path.replace("/", "_"))
@pytest.mark.scenario("Strony 404 zwracają 404 i są logowane w rejestrze brakujących linków")
def test_error_pages_404(page, runtime_env, admin_panel, path: str):
    status_code = _request_status(runtime_env.base_url, path)
    assert status_code == 404, f"Dla ścieżki '{path}' oczekiwano kodu 404, znaleziono {status_code}."

    assert _missing_link_is_logged(page, admin_panel, path), (
        f"Brak wpisu dla ścieżki '{path}' w rejestrze URL 404 w adminie."
    )
