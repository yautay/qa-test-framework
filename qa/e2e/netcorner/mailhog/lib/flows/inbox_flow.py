from __future__ import annotations

import re
import time

from playwright.sync_api import BrowserContext, Locator, Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.mailhog.lib.allure_decorators import step
from qa.e2e.netcorner.mailhog.lib.config import MailInboxEnv, MailInboxProvider, resolve_mail_inbox_env
from qa.e2e.netcorner.mailhog.lib.mail_subjects import MailSubjectPattern, MailSubjects

_PASSWORD_RESET_LINK_REGEX = r"(?i)https?://[^\s\"'<>]*(reset|odzysk|hasl|password)[^\s\"'<>]*"


class MailInboxService:
    def __init__(self, runtime_env: RuntimeEnv) -> None:
        self.__runtime_env = runtime_env
        self.__mail_env = resolve_mail_inbox_env(runtime_env.server_name)

    @property
    def inbox_env(self) -> MailInboxEnv:
        return self.__mail_env

    @step("Pobieram link z maila: {subject.key}")
    def get_link_from_subject(
        self,
        *,
        context: BrowserContext,
        recipient: str,
        subject: MailSubjectPattern,
        link_regex: str,
        timeout_ms: int = 60_000,
    ) -> str:
        mail_page = context.new_page()
        try:
            self.__open_inbox(mail_page)
            self.__authenticate_if_required(mail_page)
            self.__open_message(mail_page, recipient=recipient, subject=subject, timeout_ms=timeout_ms)
            return self.__extract_link(mail_page, link_regex)
        finally:
            mail_page.close()

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

    @step("Otwieram skrzynkę mailową")
    def __open_inbox(self, page: Page) -> None:
        page.goto(self.__mail_env.base_url, wait_until="domcontentloaded")

    @step("Loguję się do skrzynki mailowej")
    def __authenticate_if_required(self, page: Page) -> None:
        if not self.__mail_env.requires_auth:
            return

        user_input = page.locator("#rcmloginuser")
        if not user_input.is_visible(timeout=3_000):
            return

        page.locator("#rcmloginuser").fill(self.__mail_env.login)
        page.locator("#rcmloginpwd").fill(self.__mail_env.password)
        submit = page.locator("#rcmloginsubmit")
        if submit.count() > 0:
            submit.click()
        else:
            page.get_by_role("button", name=re.compile("zaloguj|login", re.IGNORECASE)).click()
        page.wait_for_load_state("domcontentloaded")

    @step("Wyszukuję wiadomość: {subject.key}")
    def __open_message(
        self,
        page: Page,
        *,
        recipient: str,
        subject: MailSubjectPattern,
        timeout_ms: int,
    ) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            self.__refresh_inbox(page)
            if self.__try_open_message_from_known_rows(page, recipient=recipient, subject=subject):
                page.wait_for_timeout(400)
                return
            if self.__try_open_message_from_subject(page, subject):
                page.wait_for_timeout(400)
                return
            page.wait_for_timeout(2_000)

        raise AssertionError(
            f"Nie znaleziono wiadomości '{subject.key}' dla odbiorcy '{recipient}' w czasie {timeout_ms} ms"
        )

    def __refresh_inbox(self, page: Page) -> None:
        if self.__mail_env.provider == MailInboxProvider.ROUNDCUBE:
            refresh = page.locator("#messagelist-header a.button.refresh, #rcmbtn109")
            if refresh.count() > 0:
                refresh.first.click()
            else:
                page.reload(wait_until="domcontentloaded")
            return

        if self.__mail_env.provider == MailInboxProvider.MAILHOG:
            refresh = page.get_by_role("button", name=re.compile("refresh|odśwież", re.IGNORECASE))
            if refresh.count() > 0:
                refresh.first.click()
            else:
                page.reload(wait_until="domcontentloaded")
            return

        page.reload(wait_until="domcontentloaded")

    def __try_open_message_from_known_rows(
        self,
        page: Page,
        *,
        recipient: str,
        subject: MailSubjectPattern,
    ) -> bool:
        row_selectors = [
            "#messagelist tbody tr",
            "table tbody tr",
            "ul li",
            ".msglist-message",
        ]

        for selector in row_selectors:
            rows = page.locator(selector)
            row_count = rows.count()
            if row_count == 0:
                continue

            for index in range(row_count):
                row = rows.nth(index)
                row_text = row.inner_text(timeout=500).strip()
                if not row_text:
                    continue

                recipient_match = recipient.lower() in row_text.lower()
                subject_match = bool(subject.compiled().search(row_text))
                if recipient_match and subject_match:
                    row.click()
                    return True

        return False

    def __try_open_message_from_subject(self, page: Page, subject: MailSubjectPattern) -> bool:
        candidate = page.get_by_text(subject.compiled()).first
        if candidate.count() == 0:
            return False
        candidate.click()
        return True

    @step("Pobieram link z treści wiadomości")
    def __extract_link(self, page: Page, link_regex: str) -> str:
        pattern = re.compile(link_regex)

        for href in self.__collect_links(page):
            if pattern.search(href):
                return href

        for text in self.__collect_text_fragments(page):
            for match in re.findall(r"https?://[^\s\"'<>]+", text):
                if pattern.search(match):
                    return match

        raise AssertionError(f"Nie znaleziono linku pasującego do regex: {link_regex}")

    @staticmethod
    def __collect_links(page: Page) -> list[str]:
        links: list[str] = []
        for container in (page, *[frame for frame in page.frames if frame != page.main_frame]):
            anchors = container.locator("a[href]")
            anchor_count = anchors.count()
            for index in range(anchor_count):
                href = anchors.nth(index).get_attribute("href")
                if href:
                    links.append(href.strip())
        return links

    @staticmethod
    def __collect_text_fragments(page: Page) -> list[str]:
        fragments: list[str] = []
        for container in (page, *[frame for frame in page.frames if frame != page.main_frame]):
            body: Locator = container.locator("body")
            if body.count() == 0:
                continue
            text = body.inner_text(timeout=1_000).strip()
            if text:
                fragments.append(text)
        return fragments
