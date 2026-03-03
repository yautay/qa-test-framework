from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderSmokeCase:
    case_id: str
    scenario: str


ORDER_SMOKE_CASES: tuple[OrderSmokeCase, ...] = ()
