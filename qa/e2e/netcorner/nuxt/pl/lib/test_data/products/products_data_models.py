from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductDataModel:
    id: int | None = None
    availability_status: AvailabilityStatus | None = None


@dataclass(frozen=True)
class AvailabilityStatus:
    status: str
    description: str


class AvailabilityStatuses:
    ONE_DAY = AvailabilityStatus(
        status="Wysyłamy najczęściej w 1 dzień roboczy",
        description="Produkt dostępny, wysyłka z magazynu głównego.",
    )

    @classmethod
    def from_status_text(cls, status_text: str) -> AvailabilityStatus:
        for value in cls.__dict__.values():
            if isinstance(value, AvailabilityStatus) and value.status == status_text:
                return value
        raise ValueError(f"Nieznany status dostępności: '{status_text}'")
