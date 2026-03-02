import re

_DNS_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")

def resolve_pl_nuxt_base_url(server_type: str, server_name: str) -> str:
    env_type = server_type.strip().lower()
    server_name = server_name.strip().lower()

    if env_type == "test":
        if not server_name:
            raise ValueError("server_name required for test environment")
        if not _DNS_LABEL.match(server_name):
            raise ValueError(f"Invalid server_name for DNS label: {server_name!r}")
        return f"https://komputronik-{server_name}.netcorner.pl"

    base_urls = {
        "demo": "https://sklep3-demo.komputronik.dev",
        "prod": "https://komputronik.pl",
        "local": "https://komputronik.local",
    }

    try:
        return base_urls[env_type].rstrip("/")
    except KeyError:
        raise ValueError(f"Unknown server_type: {server_type!r}")