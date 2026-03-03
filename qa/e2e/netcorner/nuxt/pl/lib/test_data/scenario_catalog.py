from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SmokeScenario:
    scenario_id: str
    test_type: str
    tags: tuple[str, ...]


def build_order_smoke_scenarios() -> Sequence[SmokeScenario]:
    return []


def collect_smoke_nodeids() -> set[str]:
    return set()


def validate_smoke_coverage(scenarios: Sequence[SmokeScenario]) -> list[str]:
    return []


def validate_smoke_mapping(scenarios: Sequence[SmokeScenario], collected: set[str]) -> list[str]:
    return []
