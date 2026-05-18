from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromoCodeSeed:
    code: str
    promotion_name: str
    type_label: str = "Promocja"


@dataclass(frozen=True)
class PromotionServiceCredentials:
    login: str
    password: str


@dataclass(frozen=True)
class ProductSetCase:
    case_id: str
    product_ids: tuple[int, ...]
