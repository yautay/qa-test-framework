from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent as FrameworkBaseComponent


class BaseComponent(FrameworkBaseComponent):
    @staticmethod
    def resolve_root(scope: Page | Locator, root_selector: str) -> Locator:
        root = scope.locator(root_selector)
        if isinstance(scope, Page):
            return root

        try:
            return root.first if root.count() > 0 else scope
        except Exception:
            return root.first

__all__ = ["BaseComponent"]
