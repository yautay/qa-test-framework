from __future__ import annotations

from urllib.parse import urlsplit

import allure
import pytest

from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.configurator_page import ConfiguratorPage
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.pages.home_page import HomePage
from qa.e2e.netcorner.nuxt.pl.lib.test_data import ConfiguratorEntryCase, configurator_entry_cases
from qa.e2e.netcorner.nuxt.pl.lib.timeouts import UI_ACTION_MS

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_configurator,
]


@allure.feature("Konfigurator zestawów")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("entry_case", configurator_entry_cases(), ids=lambda case: case.case_id)
@pytest.mark.scenario("Wejście do konfiguratora z dostępnych punktów wejścia")
def test_configurator_entry_points(page, runtime_env, entry_case: ConfiguratorEntryCase):
    configurator_page = _open_configurator(page=page, base_url=runtime_env.base_url, entry_case=entry_case)

    actual_header_text = configurator_page.content.actions.get_configuration_section_title().strip()
    assert actual_header_text == entry_case.expected_header_text, (
        f"Niepoprawny nagłówek konfiguratora dla scenariusza '{entry_case.scenario_name}'. "
        f"Oczekiwano '{entry_case.expected_header_text}', otrzymano '{actual_header_text}'."
    )

    actual_path = _normalize_path(urlsplit(page.url).path)
    expected_path = _normalize_path(entry_case.expected_path)
    assert actual_path == expected_path, (
        f"Niepoprawna ścieżka URL dla scenariusza '{entry_case.scenario_name}'. "
        f"Oczekiwano '{expected_path}', otrzymano '{actual_path}'."
    )


def _open_configurator(*, page, base_url: str, entry_case: ConfiguratorEntryCase) -> ConfiguratorPage:
    if entry_case.entry_point == "banner":
        return HomePage(page, base_url).open().wait_loaded(timeout=UI_ACTION_MS).open_configurator_from_banner()
    if entry_case.entry_point == "swipe":
        return HomePage(page, base_url).open().wait_loaded(timeout=UI_ACTION_MS).open_configurator_from_swiper()
    if entry_case.entry_point == "url":
        return ConfiguratorPage(page, base_url).open(entry_case.start_path).wait_loaded(timeout=UI_ACTION_MS)
    raise ValueError(f"Unsupported configurator entry point: {entry_case.entry_point}")


def _normalize_path(path: str) -> str:
    return f"/{path.strip('/')}"
