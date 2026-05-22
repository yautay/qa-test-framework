from __future__ import annotations

import uuid

from qa.e2e.netcorner.nuxt.pl.lib.test_data.advanced_configurator.advanced_configurator_data_models import (
    AdvancedConfiguratorCase,
    AdvancedConfiguratorData,
    ConfiguratorEntryCase,
)


class AdvancedConfiguratorDataBuilder:
    def __init__(self) -> None:
        unique = uuid.uuid4().hex[:6]
        self._email = f"client_{unique}@test.pl"
        self._password = f"a1{uuid.uuid4().hex[:8]}"
        self._password_changed = f"b2{uuid.uuid4().hex[:8]}"
        self._business_offer = False
        self._accept_required_terms = False
        self._accept_marketing = False
        self._nip = ""
        self._phone = ""

    def with_business_offer(self) -> AdvancedConfiguratorDataBuilder:
        self._business_offer = True
        self._nip = "7770020640"
        self._phone = "791233545"
        return self

    def with_required_terms(self) -> AdvancedConfiguratorDataBuilder:
        self._accept_required_terms = True
        return self

    def with_marketing(self) -> AdvancedConfiguratorDataBuilder:
        self._accept_marketing = True
        return self

    def build(self) -> AdvancedConfiguratorData:
        return AdvancedConfiguratorData(
            email=self._email,
            password=self._password,
            password_changed=self._password_changed,
            business_offer=self._business_offer,
            accept_required_terms=self._accept_required_terms,
            accept_marketing=self._accept_marketing,
            nip=self._nip,
            phone=self._phone,
        )


def valid_advanced_configurator_cases() -> list[AdvancedConfiguratorCase]:
    return [
        AdvancedConfiguratorCase(
            case_id="pl_terms_marketing_business",
            factory=lambda: (
                AdvancedConfiguratorDataBuilder().with_business_offer().with_required_terms().with_marketing().build()
            ),
        ),
        AdvancedConfiguratorCase(
            case_id="pl_terms_marketing",
            factory=lambda: AdvancedConfiguratorDataBuilder().with_required_terms().with_marketing().build(),
        ),
        AdvancedConfiguratorCase(
            case_id="pl_terms_only",
            factory=lambda: AdvancedConfiguratorDataBuilder().with_required_terms().build(),
        ),
    ]


def invalid_advanced_configurator_cases() -> list[AdvancedConfiguratorCase]:
    return [
        AdvancedConfiguratorCase(
            case_id="pl_marketing_business",
            factory=lambda: AdvancedConfiguratorDataBuilder().with_business_offer().with_marketing().build(),
        ),
        AdvancedConfiguratorCase(
            case_id="pl_marketing",
            factory=lambda: AdvancedConfiguratorDataBuilder().with_marketing().build(),
        ),
        AdvancedConfiguratorCase(
            case_id="pl_only",
            factory=lambda: AdvancedConfiguratorDataBuilder().build(),
        ),
    ]


def prod_registered_advanced_configurator_client() -> AdvancedConfiguratorData:
    return AdvancedConfiguratorData(
        email="nc-test-user@komputronik.pl",
        password="UjK_$CE4pCRB9hjn$_eX",
        password_changed="",
        business_offer=True,
        accept_required_terms=True,
        accept_marketing=True,
        nip="7770020640",
        phone="791233545",
    )


def configurator_entry_cases() -> list[ConfiguratorEntryCase]:
    expected_path = "/advanced-configurator"
    expected_header_text = "Konfigurator komputera PC"
    return [
        ConfiguratorEntryCase(
            case_id="pl_configurator_entry_banner",
            scenario_name="configurator_entry_banner",
            entry_point="banner",
            start_path="/",
            expected_path=expected_path,
            expected_header_text=expected_header_text,
            requires_home_navigation=True,
        ),
        ConfiguratorEntryCase(
            case_id="pl_configurator_entry_swipe",
            scenario_name="configurator_entry_swipe",
            entry_point="swipe",
            start_path="/",
            expected_path=expected_path,
            expected_header_text=expected_header_text,
            requires_home_navigation=True,
        ),
        ConfiguratorEntryCase(
            case_id="pl_configurator_entry_url",
            scenario_name="configurator_entry_url",
            entry_point="url",
            start_path="/advanced-configurator",
            expected_path=expected_path,
            expected_header_text=expected_header_text,
            requires_home_navigation=False,
        ),
    ]
