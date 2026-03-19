from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from framework.url_resolver.url_resolver import EnvUrls, url_resolver

_DEMO_INBOX_URL = "https://vpopmail.ktr.pl/roundcube/?_task=mail&_mbox=INBOX"
_DEMO_LOGIN = "kryzys-demo@ktr.pl"
_DEMO_PASSWORD = "NkUxY7vdgAcTMKoxfqcdhknHq"


class MailInboxProvider(StrEnum):
    ROUNDCUBE = "roundcube"
    MAILHOG = "mailhog"


@dataclass(frozen=True)
class MailInboxEnv:
    provider: MailInboxProvider
    base_url: str
    requires_auth: bool
    login: str = ""
    password: str = ""


def resolve_mail_inbox_env(server_name: str) -> MailInboxEnv:
    token = str(server_name or "").strip().lower()
    if not token:
        raise ValueError("server_name is required to resolve mail inbox URL")

    if token == "demo":
        return MailInboxEnv(
            provider=MailInboxProvider.ROUNDCUBE,
            base_url=_DEMO_INBOX_URL,
            requires_auth=True,
            login=_DEMO_LOGIN,
            password=_DEMO_PASSWORD,
        )

    resolver = url_resolver(
        EnvUrls(
            prod="https://mail-prod.netcorner.pl",
            demo=_DEMO_INBOX_URL,
            test_template="https://mail-{host}.netcorner.pl",
            local="https://mailhog.local",
        )
    )
    resolved_base_url = resolver(token).rstrip("/")

    provider = MailInboxProvider.MAILHOG
    return MailInboxEnv(
        provider=provider,
        base_url=resolved_base_url,
        requires_auth=False,
    )
