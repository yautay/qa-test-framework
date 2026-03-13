from __future__ import annotations

import pytest

from framework.targeting import (
    resolve_reference_base_url,
    resolve_target_context,
    resolve_target_id_for_nodeid,
)

pytestmark = [pytest.mark.aso]


def test_resolve_target_id_for_wp_path() -> None:
    target_id = resolve_target_id_for_nodeid("qa/visual/netcorner/wp/nano/test_wp_nano_visual.py::test_wp_nano_visual")

    assert target_id == "netcorner-wp-nano"


def test_resolve_target_id_for_nuxt_visual_path() -> None:
    target_id = resolve_target_id_for_nodeid(
        "qa/visual/netcorner/nuxt/pl/layers/test_layers_visual.py::test_layers_visual"
    )

    assert target_id == "netcorner-nuxt-pl"


def test_resolve_target_context_prefers_explicit_base_url() -> None:
    context = resolve_target_context(
        nodeid="qa/visual/netcorner/wp/carrer/test_wp_carrer_visual.py::test_wp_carrer_visual",
        server_name="weryfikacja.alfa",
        explicit_base_url="https://example.override",
    )

    assert context.base_url == "https://example.override"
    assert context.explicit_override is True
    assert context.source == "explicit_base_url"


def test_resolve_target_context_for_wp_target_mapping() -> None:
    context = resolve_target_context(
        nodeid="qa/visual/netcorner/wp/gaming/test_wp_gaming_visual.py::test_wp_gaming_visual",
        server_name="weryfikacja.alfa",
    )

    assert context.target_id == "netcorner-wp-gaming"
    assert context.base_url == "https://wp-komputronik-gamingweryfikacja.alfa.netcorner.pl"
    assert context.source == "target_mapping"
    assert context.explicit_override is False


def test_resolve_target_context_errors_when_target_missing() -> None:
    with pytest.raises(ValueError, match="Cannot resolve target"):
        resolve_target_context(
            nodeid="qa/visual/unknown/test_unknown_visual.py::test_unknown_visual",
            server_name="weryfikacja.alfa",
        )


def test_resolve_reference_base_url_alias() -> None:
    base_url, reference_host, source = resolve_reference_base_url("demo")

    assert base_url == "https://sklep3-demo.komputronik.dev"
    assert reference_host == "demo"
    assert source == "reference_alias"
