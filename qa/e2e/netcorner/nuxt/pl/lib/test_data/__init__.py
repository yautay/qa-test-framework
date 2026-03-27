"""Test data for NUXT app."""

from qa.e2e.netcorner.nuxt.pl.lib.test_data.client import (
    AuthSessionCase,
    ClientCase,
    ClientData,
    ClientDataBuilder,
    auth_session_cases,
    invalid_client_cases,
    prod_registered_client,
    valid_client_cases,
)
from qa.e2e.netcorner.nuxt.pl.lib.test_data.advanced_configurator import (
    AdvancedConfiguratorCase,
    AdvancedConfiguratorData,
    AdvancedConfiguratorDataBuilder,
    invalid_advanced_configurator_cases,
    prod_registered_advanced_configurator_client,
    valid_advanced_configurator_cases,
)

__all__ = [
    "AuthSessionCase",
    "ClientCase",
    "ClientData",
    "ClientDataBuilder",
    "auth_session_cases",
    "invalid_client_cases",
    "prod_registered_client",
    "valid_client_cases",
    "AdvancedConfiguratorCase",
    "AdvancedConfiguratorData",
    "AdvancedConfiguratorDataBuilder",
    "invalid_advanced_configurator_cases",
    "prod_registered_advanced_configurator_client",
    "valid_advanced_configurator_cases",
]
