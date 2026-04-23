from __future__ import annotations

import re

from playwright.sync_api import Locator, Page


def _is_visible(locator: Locator) -> bool:
    target = locator.first
    return target.count() > 0 and target.is_visible()


def _order_address_dialog_root(page: Page, heading_pattern: str) -> Locator:
    return page.locator('[data-name="OrderAddressDialog"]:visible').filter(
        has=page.get_by_role("heading", name=re.compile(heading_pattern, re.IGNORECASE))
    )
