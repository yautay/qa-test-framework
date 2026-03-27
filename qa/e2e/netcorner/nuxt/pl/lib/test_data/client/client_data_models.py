from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ClientData:
    email: str
    password: str
    password_changed: str
    business_offer: bool = False
    accept_required_terms: bool = False
    accept_marketing: bool = False
    nip: str = ""
    phone: str = ""


@dataclass(frozen=True)
class ClientCase:
    case_id: str
    factory: Callable[[], "ClientData"]


@dataclass(frozen=True)
class AuthSessionCase:
    case_id: str
    authenticated: bool
