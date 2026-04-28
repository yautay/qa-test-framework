from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


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
