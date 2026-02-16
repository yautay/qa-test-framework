import re
from dataclasses import dataclass

_DNS_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True)
class EnvUrls:
    prod: str
    demo: str
    test_template: str  # np. "https://komputronik-{host}.netcorner.pl"


def url_resolver(cfg: EnvUrls):
    def resolve(env: str, server_name: str = "") -> str:
        env_key = env.strip().lower()

        if env_key == "prod":
            return cfg.prod
        elif env_key == "demo":
            return cfg.demo
        elif env_key == "test":
            name = server_name.strip().lower()
            if not name:
                raise ValueError("server_name is required for test environment")
            if not _DNS_LABEL.match(name):
                raise ValueError(f"Invalid server_name (DNS label expected): {server_name!r}")
            return cfg.test_template.format(host=name)

        raise ValueError(f"Unknown environment: {env!r}")

    return resolve
