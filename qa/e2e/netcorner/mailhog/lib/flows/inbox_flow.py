from __future__ import annotations

import time

from playwright.sync_api import BrowserContext

from framework.env import RuntimeEnv
from qa.e2e.netcorner.mailhog.lib.allure_decorators import step
from qa.e2e.netcorner.mailhog.lib.config import MailInboxEnv, resolve_mail_inbox_env
from qa.e2e.netcorner.mailhog.lib.mail_subjects import MailSubjectPattern, MailSubjects
from qa.e2e.netcorner.mailhog.lib.page_objects.pages.inbox_page import InboxPage

_PASSWORD_RESET_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*(reset|odzysk|hasl|password)[^\s\"'<>]*"
_ORDER_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*(zamow|order|checkout|status|details)[^\s\"'<>]*"


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
        timeout_ms: int = 60_000,
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
        timeout_ms: int = 60_000,
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
        timeout_ms: int = 60_000,
        link_regex: str = _ORDER_LINK_REGEX,
    ) -> str:
        return self.get_link_from_subject(
            context=context,
            recipient=recipient,
            subject=MailSubjects.order_shop_number(shop_host=shop_host, order_number=order_number),
            link_regex=link_regex,
            timeout_ms=timeout_ms,
        )

    @step("Loguję się do skrzynki mailowej")
    def __authenticate_if_required(self, inbox_page: InboxPage) -> None:
        if not self.__mail_env.requires_auth:
            return

        if not inbox_page.is_login_form_visible():
            return

        inbox_page.login(self.__mail_env.login, self.__mail_env.password)

    @step("Wyszukuję wiadomość: {subject}")
    def __open_message(
        self,
        inbox_page: InboxPage,
        *,
        recipient: str,
        subject: MailSubjectPattern,
        timeout_ms: int,
    ) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            inbox_page.refresh_messages()
            if inbox_page.open_message(recipient=recipient, subject=subject):
                return
            inbox_page.page.wait_for_timeout(2_000)

        raise AssertionError(
            f"Nie znaleziono wiadomości '{subject.key}' dla odbiorcy '{recipient}' w czasie {timeout_ms} ms"
        )
