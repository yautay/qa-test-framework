from __future__ import annotations

from playwright.sync_api import Locator, Page

from framework.base.page_objects import BaseComponent as FrameworkBaseComponent


class BaseComponent(FrameworkBaseComponent):
    @staticmethod
    def _scope_matches_root(scope: Locator, root_selector: str) -> bool:
        return bool(scope.evaluate("(node, selector) => node instanceof Element && node.matches(selector)", root_selector))

    @staticmethod
    def resolve_root(scope: Page | Locator, root_selector: str) -> Locator:
        if isinstance(scope, Page):
            return scope.locator(root_selector)
        if BaseComponent._scope_matches_root(scope, root_selector):
            return scope
        return scope.locator(root_selector)


__all__ = ["BaseComponent"]
