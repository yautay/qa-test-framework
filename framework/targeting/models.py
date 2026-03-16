from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetContext:
    target_id: str
    base_url: str
    source: str
    explicit_override: bool
