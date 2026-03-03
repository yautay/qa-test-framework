from __future__ import annotations

from typing import Any

from ..state import TEXT_MAX_LENGTH, _normalize_text


def _validated_text(value: Any, field_name: str) -> str:
    text = _normalize_text(value, trim=True)
    if len(text) > TEXT_MAX_LENGTH:
        raise ValueError(f"{field_name} exceeds {TEXT_MAX_LENGTH} characters")
    return text


def _as_non_empty_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid field: {key}")
    return value.strip()
