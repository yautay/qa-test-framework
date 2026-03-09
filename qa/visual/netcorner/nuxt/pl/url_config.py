from __future__ import annotations

from framework.url_resolver.url_resolver import EnvUrls, url_resolver

resolve_pl = url_resolver(
    EnvUrls(
        prod="https://komputronik.pl",
        demo="https://sklep3-demo.komputronik.dev",
        test_template="https://komputronik-{host}.netcorner.pl",
    )
)

_REFERENCE_ENV_ALIASES = {"demo", "prod", "local"}


def resolve_runtime_base_url(server_type: str, server_name: str) -> str:
    return resolve_pl(server_type, server_name).rstrip("/")


def resolve_reference_base_url(reference_host: str) -> tuple[str, str, str]:
    token = str(reference_host or "").strip().lower()
    if not token:
        raise ValueError("reference_host is required for reference pass")
    if token in _REFERENCE_ENV_ALIASES:
        return resolve_pl(token, "").rstrip("/"), token, "reference_alias"
    return resolve_pl("test", token).rstrip("/"), token, "reference_host"
