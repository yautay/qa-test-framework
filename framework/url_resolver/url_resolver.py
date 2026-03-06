import re
from dataclasses import dataclass

_DNS_HOSTNAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?" r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*$")


@dataclass(frozen=True)
class EnvUrls:
    prod: str
    demo: str
    test_template: str  # np. "https://komputronik-{host}.netcorner.pl"
    local: str = ""


def url_resolver(cfg: EnvUrls):
    def resolve(target: str) -> str:
        token = target.strip().lower()

        if token == "prod":
            return cfg.prod.rstrip("/")
        elif token == "demo":
            return cfg.demo.rstrip("/")
        elif token == "local":
            if not cfg.local:
                raise ValueError("Local URL is not configured")
            return cfg.local.rstrip("/")

        if not _DNS_HOSTNAME.match(token):
            raise ValueError(f"Invalid server_name (DNS hostname expected): {target!r}")
        try:
            return cfg.test_template.format(host=token).rstrip("/")
        except KeyError as e:
            raise ValueError(f"Invalid test_template {cfg.test_template!r}; expected placeholder {{host}}") from e

    return resolve
