from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class AdminOrderProduct:
    """Single product line as read from admin order detail page."""

    name: str
    quantity: int
    unit_price_gross: Decimal


@dataclass(frozen=True)
class AdminOrderData:
    """All data readable from the admin order detail page."""

    order_number: str
    status: str
    summary_price_gross: Decimal
    shipping_price: Decimal
    purchaser_raw: list[str] = field(default_factory=list)
    receiver_raw: list[str] = field(default_factory=list)
    products: list[AdminOrderProduct] = field(default_factory=list)
    parameter_card: str = ""
    order_comment: str = ""
    nip: str = ""


__all__ = ["AdminOrderData", "AdminOrderProduct"]
