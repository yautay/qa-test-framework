from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


@dataclass
class AdvancedConfiguratorData:
    email: str
    password: str
    password_changed: str
    business_offer: bool = False
    accept_required_terms: bool = False
    accept_marketing: bool = False
    nip: str = ""
    phone: str = ""


@dataclass(frozen=True)
class AdvancedConfiguratorCase:
    case_id: str
    factory: Callable[[], AdvancedConfiguratorData]


@dataclass(frozen=True)
class ConfiguratorEntryCase:
    case_id: str
    scenario_name: str
    entry_point: Literal["banner", "swipe", "url"]
    start_path: str
    expected_path: str
    expected_header_text: str
    requires_home_navigation: bool
