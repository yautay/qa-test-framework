from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent as FrameworkBaseComponent


class BaseComponent(FrameworkBaseComponent):
    @staticmethod
    def resolve_root(scope: Page | Locator, root_selector: str) -> Locator:
        return scope.locator(root_selector)


__all__ = ["BaseComponent"]
