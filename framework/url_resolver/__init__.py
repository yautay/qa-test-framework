import re

_DNS_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def resolve_pl_nuxt_base_url(server_name: str) -> str:
    token = server_name.strip().lower()

    base_urls = {
        "demo": "https://sklep3-demo.komputronik.dev",
        "prod": "https://komputronik.pl",
        "local": "https://komputronik.local",
    }
    if token in base_urls:
        return base_urls[token].rstrip("/")

    if not token:
        raise ValueError("server_name required")
    if not _DNS_LABEL.match(token):
        raise ValueError(f"Invalid server_name for DNS label: {server_name!r}")
    return f"https://komputronik-{token}.netcorner.pl"
