from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComponentContext(str, Enum):
    CHECKOUT = "checkout"
    ACCOUNT = "account"


@dataclass(frozen=True)
class ReceiverSelectionRequest:
    delivery_kind: str
    receiver_data: dict[str, str]
    delivery_location: str | None = None
    delivery_point_name: str | None = None
    context: ComponentContext = ComponentContext.CHECKOUT
