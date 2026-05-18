from __future__ import annotations

import base64
from dataclasses import dataclass

from framework.url_resolver.url_resolver import EnvUrls, url_resolver

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------
# Login: at.tester
# Password: base64-encoded — decoded at runtime (same pattern as Selenium repo)
_ADMIN_LOGIN = "at.tester"
_ADMIN_PASSWORD_B64 = "cDN5RW5hOEdmQTdHZE1SOFRCS1RtNG15VDc="

# Sales channel ID for komputronik.pl (PL context)
ADMIN_SALES_CHANNEL_PL = 1


def decode_admin_password() -> str:
    return base64.b64decode(_ADMIN_PASSWORD_B64).decode("utf-8")


# ---------------------------------------------------------------------------
# URL resolution
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdminEnv:
    base_url: str
    login: str
    password: str
    sales_channel_id: int


def resolve_admin_env(server_name: str, sales_channel_id: int = ADMIN_SALES_CHANNEL_PL) -> AdminEnv:
    """Resolve admin panel base URL from server_name.

    URL pattern mirrors settings.py in nc-functional-tests-py:
        test_admin_server_url = "https://admin-" + server_name + ".netcorner.pl/"

    For komputronik-galak specifically, the admin is reachable at:
        https://admin-galak.test.netcorner.pl/admin.php
    (the resolver strips the 'komputronik-' prefix per the env naming convention).
    """
    token = str(server_name or "").strip().lower()
    if not token:
        raise ValueError("server_name is required to resolve admin URL")

    resolver = url_resolver(
        EnvUrls(
            prod="https://admin-prod.netcorner.pl",
            demo="https://sklep-admin-demo.ktr.pl",
            test_template="https://admin-{host}.netcorner.pl",
            local="https://admin.local",
        )
    )
    base_url = resolver(token).rstrip("/")

    return AdminEnv(
        base_url=base_url,
        login=_ADMIN_LOGIN,
        password=decode_admin_password(),
        sales_channel_id=sales_channel_id,
    )


__all__ = ["AdminEnv", "ADMIN_SALES_CHANNEL_PL", "decode_admin_password", "resolve_admin_env"]
