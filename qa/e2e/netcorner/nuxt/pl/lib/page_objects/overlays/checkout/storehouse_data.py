from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StorehouseData:
    data_id: str
    name: str
