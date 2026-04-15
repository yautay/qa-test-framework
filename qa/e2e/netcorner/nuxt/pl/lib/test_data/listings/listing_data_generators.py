from __future__ import annotations

from qa.e2e.netcorner.nuxt.pl.lib.test_data.listings.listings_data_models import ListingsData
from qa.e2e.netcorner.nuxt.pl.lib.test_data.products.products_data_models import AvailabilityStatuses


class ListingDataBuilder:
    def __init__(self) -> None:
        self.category_url = ""
        self.filters = None

def first_aviable_laptop_case() -> ListingsData:
    return ListingsData(
        category_url="search-filter/5022/laptopy-do-gier",
        product_availability_status=AvailabilityStatuses.ONE_DAY,
        )

