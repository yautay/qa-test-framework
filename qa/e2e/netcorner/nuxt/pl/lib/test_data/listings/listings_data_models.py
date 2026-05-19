from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import AvailabilityStatus


@dataclass
class ListingsData:
    category_url: str
    product_availability_status: AvailabilityStatus
    filters: Filter | None = None


@dataclass(frozen=True)
class Filter:
    filter_type: FilterTypes | None = None
    filter_value: Any | None = None


@dataclass(frozen=True)
class FilterTypes:
    PRODUCER = "producer"


@dataclass(frozen=True)
class ListingCase:
    case_id: str
    factory: Callable[[], ListingsData]
