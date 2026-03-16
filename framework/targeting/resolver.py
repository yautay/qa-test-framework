from __future__ import annotations

from framework.targeting.models import TargetContext
from framework.targeting.registry import all_target_definitions, get_target_definition
from framework.url_resolver.url_resolver import url_resolver

_REFERENCE_TARGET_ID = "netcorner-nuxt-pl"


def _normalize_nodeid(nodeid: str) -> str:
    token = str(nodeid or "").strip().replace("\\", "/")
    if "::" in token:
        token = token.split("::", 1)[0]
    return token.lstrip("/")


def resolve_target_id_for_nodeid(nodeid: str) -> str | None:
    normalized = _normalize_nodeid(nodeid)
    if not normalized:
        return None
    matches: list[str] = []
    for definition in all_target_definitions():
        for prefix in definition.path_prefixes:
            if normalized.startswith(prefix):
                matches.append(definition.target_id)
                break
    unique = sorted(set(matches))
    if not unique:
        return None
    if len(unique) > 1:
        raise ValueError(f"Ambiguous target for nodeid={nodeid!r}: {', '.join(unique)}")
    return unique[0]


def resolve_base_url(*, target_id: str, server_name: str) -> str:
    definition = get_target_definition(target_id)
    resolve = url_resolver(definition.urls)
    return resolve(str(server_name or "").strip()).rstrip("/")


def resolve_target_context(
    *,
    nodeid: str,
    server_name: str,
    explicit_base_url: str = "",
    marker_target: str = "",
) -> TargetContext:
    explicit = str(explicit_base_url or "").strip()
    if explicit:
        target_id = str(marker_target or "").strip() or "explicit-base-url"
        return TargetContext(
            target_id=target_id,
            base_url=explicit.rstrip("/"),
            source="explicit_base_url",
            explicit_override=True,
        )

    resolved_target = str(marker_target or "").strip() or resolve_target_id_for_nodeid(nodeid)
    if not resolved_target:
        raise ValueError(
            f"Cannot resolve target for nodeid={nodeid!r}; add @pytest.mark.target('<id>') or map path prefix"
        )

    base_url = resolve_base_url(target_id=resolved_target, server_name=server_name)
    return TargetContext(
        target_id=resolved_target,
        base_url=base_url,
        source="target_mapping",
        explicit_override=False,
    )


def resolve_reference_base_url(reference_host: str) -> tuple[str, str, str]:
    token = str(reference_host or "").strip().lower()
    if not token:
        raise ValueError("reference_host is required for reference pass")

    source = "reference_alias" if token in {"demo", "prod", "local"} else "reference_host"
    resolved = resolve_base_url(target_id=_REFERENCE_TARGET_ID, server_name=token)
    return resolved, token, source
