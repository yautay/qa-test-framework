from __future__ import annotations

from dataclasses import dataclass

from framework.url_resolver.url_resolver import EnvUrls


@dataclass(frozen=True)
class TargetDefinition:
    target_id: str
    urls: EnvUrls
    path_prefixes: tuple[str, ...]


_TARGETS: tuple[TargetDefinition, ...] = (
    TargetDefinition(
        target_id="netcorner-nuxt-pl",
        urls=EnvUrls(
            prod="https://komputronik.pl",
            demo="https://sklep3-demo.komputronik.dev",
            test_template="https://komputronik-{host}.netcorner.pl",
            local="https://komputronik.local",
        ),
        path_prefixes=(
            "qa/visual/netcorner/nuxt/pl/",
            "qa/e2e/netcorner/nuxt/pl/",
        ),
    ),
    TargetDefinition(
        target_id="netcorner-nuxt-b2b",
        urls=EnvUrls(
            prod="https://bi-to-bi.pl",
            demo="https://sklep-bi-to-bi-demo.komputronik.dev",
            test_template="https://bi-to-bi-{host}.netcorner.pl",
            local="https://bi-to-bi.local",
        ),
        path_prefixes=("qa/e2e/netcorner/nuxt/b2b/",),
    ),
    TargetDefinition(
        target_id="netcorner-wp-nano",
        urls=EnvUrls(
            prod="https://nano.komputronik.pl/",
            demo="https://nano-demo.ktr.pl",
            test_template="https://wp-nano-komputronik-{host}.netcorner.pl",
        ),
        path_prefixes=("qa/visual/netcorner/wp/nano/",),
    ),
    TargetDefinition(
        target_id="netcorner-wp-gaming",
        urls=EnvUrls(
            prod="https://gaming.komputronik.pl/",
            demo="https://gaming-demo.ktr.pl",
            test_template="https://wp-komputronik-gaming-{host}.netcorner.pl",
        ),
        path_prefixes=("qa/visual/netcorner/wp/gaming/",),
    ),
    TargetDefinition(
        target_id="netcorner-wp-carrer",
        urls=EnvUrls(
            prod="https://kariera.komputronik.pl/",
            demo="https://kariera-demo.ktr.pl",
            test_template="https://wp-kariera-komputronik-{host}.netcorner.pl",
        ),
        path_prefixes=("qa/visual/netcorner/wp/carrer/",),
    ),
)


def all_target_definitions() -> tuple[TargetDefinition, ...]:
    return _TARGETS


def get_target_definition(target_id: str) -> TargetDefinition:
    token = str(target_id or "").strip()
    for definition in _TARGETS:
        if definition.target_id == token:
            return definition
    raise ValueError(f"Unknown target_id: {target_id!r}")
