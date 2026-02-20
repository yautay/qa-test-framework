from __future__ import annotations

from dataclasses import dataclass

try:
    from enum import StrEnum
except ImportError:  # Python < 3.11
    from enum import Enum as _Enum

    class StrEnum(str, _Enum):
        def __str__(self) -> str:
            return str(self.value)


class ComponentContext(StrEnum):
    CHECKOUT = "checkout"
    ACCOUNT = "account"


@dataclass(frozen=True)
class ReceiverSelectionRequest:
    delivery_kind: str
    receiver_data: dict[str, str]
    delivery_location: str | None = None
    delivery_point_name: str | None = None
    context: ComponentContext = ComponentContext.CHECKOUT
