from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request

from playwright.sync_api import BrowserContext

from framework.env import RuntimeEnv
from qa.e2e.netcorner.mailhog.lib.allure_decorators import step
from qa.e2e.netcorner.mailhog.lib.config import MailInboxEnv, MailInboxProvider, resolve_mail_inbox_env
from qa.e2e.netcorner.mailhog.lib.mail_subjects import MailSubjectPattern, MailSubjects
from qa.e2e.netcorner.mailhog.lib.page_objects.pages.inbox_page import InboxPage

_PASSWORD_RESET_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*(reset|odzysk|hasl|password)[^\s\"'<>]*"
_ORDER_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*(zamow|order|checkout|status|details)[^\s\"'<>]*"
_MAILHOG_LOOKUP_TIMEOUT_MS = 45_000
_MAILHOG_INITIAL_REFRESH_DELAY_MS = 1_000
_MAILHOG_REFRESH_CURVE_BEND = 2.0
_MAILHOG_REFRESH_MAX_RATIO = 0.30
_MAILHOG_LAST_REFRESH_BEFORE_DEADLINE_MS = 1_000

# Dynamic MailHog refresh backoff for timeout=30s.
# Legend: '|' refresh tick, 'x' timeout/deadline.
# Final refresh is pinned to 1s before deadline.
# Axis:
# 0s            5s            10s           15s           20s           25s          30s
#
# bend=1.2
# |   |    |    |      |        |           |              || x
# ticks: 0.0, 2.0, 4.329, 7.161, 10.684, 15.146, 20.889, 28.394, 29.0
#
# bend=2.0
# |   |   |   |    |    |      |       |         |          | x
# ticks: 0.0, 2.0, 4.037, 6.19, 8.551, 11.241, 14.434, 18.401, 23.598, 29.0
#
# bend=3.0
# |   |   |   |   |    |   |    |      |       |          | | x
# ticks: 0.0, 2.0, 4.002, 6.022, 8.09, 10.256, 12.595, 15.223, 18.333, 22.272, 27.75, 29.0
#
# initial=1s
# | | | | |  | |  |   |   |    |     |       |           |  | x
# ticks: 0.0, 1.0, 2.01, 3.052, 4.15, 5.331, 6.63, 8.093, 9.784, 11.794, 14.262, 17.409, 21.608, 27.536, 29.0
#
# initial=2s
# |   |   |   |    |    |      |       |         |          | x
# ticks: 0.0, 2.0, 4.037, 6.19, 8.551, 11.241, 14.434, 18.401, 23.598, 29.0
#
# initial=4s
# |       |       |        |         |            |         | x
# ticks: 0.0, 4.0, 8.115, 12.59, 17.734, 24.005, 29.0
#
# ratio=0.20
# |   |   |   |    |   |    |     |     |      |        |   | x
# ticks: 0.0, 2.0, 4.017, 6.088, 8.252, 10.554, 13.049, 15.805, 18.915, 22.505, 26.756, 29.0
#
# ratio=0.35
# |   |   |   |    |    |      |       |         |          | x
# ticks: 0.0, 2.0, 4.037, 6.19, 8.551, 11.241, 14.434, 18.401, 23.598, 29.0
#
# ratio=0.50
# |   |   |    |    |     |       |           |             | x
# ticks: 0.0, 2.0, 4.057, 6.294, 8.866, 12.001, 16.081, 21.816, 29.0
#
# mix-fast (initial=1s, bend=1.2, ratio=0.20)
# | | |  | |  |   |   |    |    |     |       |        |    | x
# ticks: 0.0, 1.0, 2.084, 3.287, 4.639, 6.171, 7.92, 9.931, 12.257, 14.964, 18.134, 21.866, 26.286, 29.0
#
# mix-balanced (initial=2s, bend=2.0, ratio=0.35)
# |   |   |   |    |    |      |       |         |          | x
# ticks: 0.0, 2.0, 4.037, 6.19, 8.551, 11.241, 14.434, 18.401, 23.598, 29.0
#
# mix-sparse (initial=4s, bend=3.0, ratio=0.50)
# |       |       |       |         |           |           | x
# ticks: 0.0, 4.0, 8.026, 12.236, 16.982, 22.977, 29.0


class MailInboxService:
    def __init__(self, runtime_env: RuntimeEnv) -> None:
        self.__runtime_env = runtime_env
        self.__mail_env = resolve_mail_inbox_env(runtime_env.server_name)

    @property
    def inbox_env(self) -> MailInboxEnv:
        return self.__mail_env

    @step("Pobieram link z maila: {subject}")
    def get_link_from_subject(
        self,
        *,
        context: BrowserContext,
        recipient: str,
        subject: MailSubjectPattern,
        link_regex: str,
        timeout_ms: int = _MAILHOG_LOOKUP_TIMEOUT_MS,
    ) -> str:
        previous_pages = tuple(context.pages)
        open_pages_before = len(context.pages)
        mail_page = context.new_page()
        open_pages_after = len(context.pages)
        if open_pages_after <= open_pages_before:
            raise AssertionError("Nie udało się otworzyć nowej karty dla skrzynki mailowej")
        mail_page.bring_to_front()
        try:
            inbox_page = InboxPage(mail_page, self.__mail_env.base_url, self.__mail_env.provider)
            inbox_page.open_inbox()
            self.__authenticate_if_required(inbox_page)
            self.__open_message(inbox_page, recipient=recipient, subject=subject, timeout_ms=timeout_ms)
            return inbox_page.extract_link(link_regex)
        finally:
            mail_page.close()
            if previous_pages:
                previous_pages[-1].bring_to_front()

    @step("Pobieram link odzyskiwania hasła")
    def get_password_reset_link(
        self,
        *,
        context: BrowserContext,
        recipient: str,
        timeout_ms: int = _MAILHOG_LOOKUP_TIMEOUT_MS,
        link_regex: str = _PASSWORD_RESET_LINK_REGEX,
    ) -> str:
        return self.get_link_from_subject(
            context=context,
            recipient=recipient,
            subject=MailSubjects.PASSWORD_RESET,
            link_regex=link_regex,
            timeout_ms=timeout_ms,
        )

    @step("Pobieram link z maila zamówienia")
    def get_order_mail_link(
        self,
        *,
        context: BrowserContext,
        recipient: str,
        shop_host: str,
        order_number: str | None = None,
        timeout_ms: int = _MAILHOG_LOOKUP_TIMEOUT_MS,
        link_regex: str = _ORDER_LINK_REGEX,
    ) -> str:
        return self.get_link_from_subject(
            context=context,
            recipient=recipient,
            subject=MailSubjects.order_shop_number(shop_host=shop_host, order_number=order_number),
            link_regex=link_regex,
            timeout_ms=timeout_ms,
        )

    @step("Zliczam wiadomości pasujące do filtra")
    def count_mails_matching(
        self,
        *,
        context: BrowserContext,
        recipient: str | None,
        subject: MailSubjectPattern,
        timeout_ms: int = _MAILHOG_LOOKUP_TIMEOUT_MS,
    ) -> int:
        return self.__with_inbox_page(
            context=context,
            action=lambda inbox_page: self.__count_messages(
                inbox_page,
                recipient=recipient,
                subject=subject,
                timeout_ms=timeout_ms,
            ),
        )

    @step("Sprawdzam obecność maila z fragmentem tematu")
    def has_mail_with_subject_containing(
        self,
        *,
        context: BrowserContext,
        recipient: str | None,
        text: str,
        timeout_ms: int = _MAILHOG_LOOKUP_TIMEOUT_MS,
    ) -> bool:
        return self.__with_inbox_page(
            context=context,
            action=lambda inbox_page: self.__has_message_with_subject_containing(
                inbox_page,
                recipient=recipient,
                text=text,
                timeout_ms=timeout_ms,
            ),
        )

    @step("Pobieram link z maila oferty koszykowej")
    def get_cart_offer_link(
        self,
        *,
        context: BrowserContext,
        recipient: str,
        timeout_ms: int = _MAILHOG_LOOKUP_TIMEOUT_MS,
        link_regex: str = _ORDER_LINK_REGEX,
    ) -> str:
        return self.get_link_from_subject(
            context=context,
            recipient=recipient,
            subject=MailSubjects.CART_OFFER,
            link_regex=link_regex,
            timeout_ms=timeout_ms,
        )

    @step("Zliczam wiadomości zawierające wskazany tekst")
    def count_mails_containing_text(self, *, text: str, recipient: str | None = None) -> int:
        items = self.__search_mailhog_messages(text)
        if recipient is None:
            return len(items)
        recipient_normalized = recipient.strip().casefold()
        return sum(
            1
            for item in items
            if any(
                str(raw_to).strip().casefold() == recipient_normalized
                for raw_to in item.get("Raw", {}).get("To", [])
            )
        )

    @step("Czekam na wiadomości zawierające wskazany tekst")
    def wait_for_mails_containing_text(
        self,
        *,
        text: str,
        recipient: str | None = None,
        min_count: int = 1,
        timeout_ms: int = _MAILHOG_LOOKUP_TIMEOUT_MS,
    ) -> int:
        started_at = time.monotonic()
        deadline = started_at + (timeout_ms / 1000)
        last_count = 0
        while time.monotonic() < deadline:
            last_count = self.count_mails_containing_text(text=text, recipient=recipient)
            if last_count >= min_count:
                return last_count
            elapsed_ms = max(0, int((time.monotonic() - started_at) * 1000))
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            wait_ms = self.__refresh_wait_ms(timeout_ms=timeout_ms, elapsed_ms=elapsed_ms, remaining_ms=remaining_ms)
            if wait_ms == 0:
                break
            time.sleep(wait_ms / 1000)
        return last_count

    @step("Loguję się do skrzynki mailowej")
    def __authenticate_if_required(self, inbox_page: InboxPage) -> None:
        if not self.__mail_env.requires_auth:
            return

        if not inbox_page.is_login_form_visible():
            return

        inbox_page.login(self.__mail_env.login, self.__mail_env.password)

    def __with_inbox_page(self, *, context: BrowserContext, action):
        previous_pages = tuple(context.pages)
        open_pages_before = len(context.pages)
        mail_page = context.new_page()
        open_pages_after = len(context.pages)
        if open_pages_after <= open_pages_before:
            raise AssertionError("Nie udało się otworzyć nowej karty dla skrzynki mailowej")
        mail_page.bring_to_front()
        try:
            inbox_page = InboxPage(mail_page, self.__mail_env.base_url, self.__mail_env.provider)
            inbox_page.open_inbox()
            self.__authenticate_if_required(inbox_page)
            return action(inbox_page)
        finally:
            mail_page.close()
            if previous_pages:
                previous_pages[-1].bring_to_front()

    def __count_messages(
        self,
        inbox_page: InboxPage,
        *,
        recipient: str | None,
        subject: MailSubjectPattern,
        timeout_ms: int,
    ) -> int:
        started_at = time.monotonic()
        deadline = started_at + (timeout_ms / 1000)
        last_count = 0
        while time.monotonic() < deadline:
            inbox_page.refresh_messages()
            last_count = inbox_page.count_messages(recipient=recipient, subject=subject)
            if last_count > 0:
                return last_count
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            elapsed_ms = max(0, int((time.monotonic() - started_at) * 1000))
            wait_ms = self.__refresh_wait_ms(timeout_ms=timeout_ms, elapsed_ms=elapsed_ms, remaining_ms=remaining_ms)
            if wait_ms == 0:
                break
            inbox_page.page.wait_for_timeout(wait_ms)
        return last_count

    def __has_message_with_subject_containing(
        self,
        inbox_page: InboxPage,
        *,
        recipient: str | None,
        text: str,
        timeout_ms: int,
    ) -> bool:
        started_at = time.monotonic()
        deadline = started_at + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            inbox_page.refresh_messages()
            if inbox_page.has_message_with_subject_containing(recipient=recipient, text=text):
                return True
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            elapsed_ms = max(0, int((time.monotonic() - started_at) * 1000))
            wait_ms = self.__refresh_wait_ms(timeout_ms=timeout_ms, elapsed_ms=elapsed_ms, remaining_ms=remaining_ms)
            if wait_ms == 0:
                break
            inbox_page.page.wait_for_timeout(wait_ms)
        return False

    def __search_mailhog_messages(self, text: str) -> list[dict]:
        if self.__mail_env.provider != MailInboxProvider.MAILHOG:
            raise AssertionError("Wyszukiwanie przez Mailhog API jest dostępne tylko dla providera MAILHOG.")

        query = urllib.parse.quote(text, safe="")
        url = f"{self.__mail_env.base_url}/api/v2/search?kind=containing&query={query}"
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(url, context=ssl_context, timeout=30) as response:
            payload = json.loads(response.read().decode())
        return payload.get("items", [])

    @step("Wyszukuję wiadomość: {subject}")
    def __open_message(
        self,
        inbox_page: InboxPage,
        *,
        recipient: str,
        subject: MailSubjectPattern,
        timeout_ms: int,
    ) -> None:
        started_at = time.monotonic()
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            inbox_page.refresh_messages()
            if inbox_page.open_message(recipient=recipient, subject=subject):
                return
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            elapsed_ms = max(0, int((time.monotonic() - started_at) * 1000))
            wait_ms = self.__refresh_wait_ms(timeout_ms=timeout_ms, elapsed_ms=elapsed_ms, remaining_ms=remaining_ms)
            if wait_ms == 0:
                break
            inbox_page.page.wait_for_timeout(wait_ms)

        raise AssertionError(
            f"Nie znaleziono wiadomości '{subject.key}' dla odbiorcy '{recipient}' w czasie {timeout_ms} ms"
        )

    @staticmethod
    def __refresh_wait_ms(*, timeout_ms: int, elapsed_ms: int, remaining_ms: int) -> int:
        if remaining_ms <= 0:
            return 0

        if timeout_ms <= 0:
            return min(_MAILHOG_INITIAL_REFRESH_DELAY_MS, remaining_ms)

        progress = min(1.0, max(0.0, elapsed_ms / timeout_ms))
        max_wait_ms = max(_MAILHOG_INITIAL_REFRESH_DELAY_MS, int(timeout_ms * _MAILHOG_REFRESH_MAX_RATIO))
        wait_ms = _MAILHOG_INITIAL_REFRESH_DELAY_MS + (
            (max_wait_ms - _MAILHOG_INITIAL_REFRESH_DELAY_MS) * (progress**_MAILHOG_REFRESH_CURVE_BEND)
        )
        wait_ms_int = max(1, int(wait_ms))

        last_refresh_elapsed_ms = max(0, timeout_ms - _MAILHOG_LAST_REFRESH_BEFORE_DEADLINE_MS)
        if elapsed_ms >= last_refresh_elapsed_ms:
            return remaining_ms

        remaining_to_last_refresh_ms = max(0, last_refresh_elapsed_ms - elapsed_ms)
        if remaining_to_last_refresh_ms > 0:
            wait_ms_int = min(wait_ms_int, remaining_to_last_refresh_ms)

        return min(wait_ms_int, remaining_ms)
