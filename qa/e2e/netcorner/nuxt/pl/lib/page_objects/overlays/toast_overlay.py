from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from playwright.sync_api import Page, expect


class ToastType(str, Enum):
    SUCCESS = "positive"
    ERROR = "error"
    INFO = "informative"
    UNKNOWN = "unknown"


class ToastInstance(str, Enum):
    USER_REGISTERED = "Konto zostało założone, zostałeś automatycznie zalogowany"
    FILL_FIELDS = "Wypełnij wszystkie pola"
    UNKNOWN = "unknown"


@dataclass
class ToastObject:
    message: str
    type: ToastType
    instance: ToastInstance


class ToastOverlay:

    def __init__(self, page: Page):
        self.page = page
        self._root = page.locator('[data-name="toast"]')

    def get_toast(self, timeout: int = 7000) -> Optional[ToastObject]:
        toast = self._root.last

        try:
            expect(toast).to_be_visible(timeout=timeout)
            message = toast.locator("div").inner_text().strip()
            classes = toast.get_attribute("class") or ""
            toast_type = self._resolve_type(classes)
            instance = self._resolve_instance(message)

        except TimeoutError:
            return None


        return ToastObject(
            message=message,
            type=toast_type,
            instance=instance
        )

    @staticmethod
    def _resolve_type(classes: str) -> ToastType:
        for t in ToastType:
            if t != ToastType.UNKNOWN and f"toast-{t.value}" in classes:
                return t
        return ToastType.UNKNOWN

    @staticmethod
    def _resolve_instance(message: str) -> ToastInstance:
        for i in ToastInstance:
            if i != ToastInstance.UNKNOWN and message == i.value:
                return i
        return ToastInstance.UNKNOWN
