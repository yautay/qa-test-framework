from __future__ import annotations

import re

from playwright.sync_api import Frame, Locator, Page

from framework.base.page_objects import BasePage
from qa.e2e.netcorner.mailhog.lib.allure_decorators import step
from qa.e2e.netcorner.mailhog.lib.config import MailInboxProvider
from qa.e2e.netcorner.mailhog.lib.mail_subjects import MailSubjectPattern


class InboxPage(BasePage):
    def __init__(self, page: Page, base_url: str, provider: MailInboxProvider) -> None:
        super().__init__(page, base_url)
        self.__provider = provider

    @step("Otwieram stronę skrzynki")
    def open_inbox(self) -> InboxPage:
        self.open().wait_loaded()
        return self

    @step("Sprawdzam formularz logowania")
    def is_login_form_visible(self) -> bool:
        if self.__provider != MailInboxProvider.ROUNDCUBE:
            return False
        return self.page.locator("#rcmloginuser").is_visible(timeout=3_000)

    @step("Wykonuję logowanie do skrzynki")
    def login(self, username: str, password: str) -> InboxPage:
        if self.__provider != MailInboxProvider.ROUNDCUBE:
            return self
        self.page.locator("#rcmloginuser").fill(username)
        self.page.locator("#rcmloginpwd").fill(password)
        submit = self.page.locator("#rcmloginsubmit")
        if submit.count() > 0:
            submit.click()
        else:
            self.page.get_by_role("button", name=re.compile("zaloguj|login", re.IGNORECASE)).click()
        self.wait_loaded()
        return self

    @step("Odświeżam skrzynkę")
    def refresh_messages(self) -> None:
        if self.__provider == MailInboxProvider.ROUNDCUBE:
            refresh = self.page.locator("#messagelist-header a.button.refresh, #rcmbtn109")
            if refresh.count() > 0:
                refresh.first.click()
                return

        if self.__provider == MailInboxProvider.MAILHOG:
            mailhog_refresh_selectors = (
                "button[title*='Refresh']",
                "button:has-text('Refresh')",
                "button .fa-refresh",
                "a[title*='Refresh']",
            )
            for selector in mailhog_refresh_selectors:
                refresh = self.page.locator(selector)
                if refresh.count() > 0:
                    refresh.first.click()
                    return

            refresh_button_by_text = self.page.get_by_role("button", name=re.compile("refresh|odśwież", re.IGNORECASE))
            if refresh_button_by_text.count() > 0:
                refresh_button_by_text.first.click()
                return

        self.reload()

    @step("Otwieram wiadomość: {subject}")
    def open_message(self, *, recipient: str, subject: MailSubjectPattern) -> bool:
        if self.__open_message_from_rows(recipient=recipient, subject=subject):
            self.page.wait_for_timeout(400)
            return True
        return False

    @step("Zliczam wiadomości spełniające filtr")
    def count_messages(
        self,
        *,
        recipient: str | None = None,
        subject: MailSubjectPattern | None = None,
    ) -> int:
        rows = self.__message_rows()
        row_count = rows.count()
        matched = 0
        for index in range(row_count):
            row = rows.nth(index)
            if recipient and not self.__row_contains_recipient_email(row=row, recipient=recipient):
                continue
            if subject and not self.__row_contains_subject(row=row, subject=subject):
                continue
            matched += 1
        return matched

    @step("Sprawdzam czy istnieje wiadomość z fragmentem tematu")
    def has_message_with_subject_containing(self, *, recipient: str | None = None, text: str) -> bool:
        rows = self.__message_rows()
        row_count = rows.count()
        for index in range(row_count):
            row = rows.nth(index)
            if recipient and not self.__row_contains_recipient_email(row=row, recipient=recipient):
                continue
            if self.__row_contains_subject_text(row=row, text=text):
                return True
        return False

    @step("Pobieram link z treści wiadomości")
    def extract_link(self, link_regex: str) -> str:
        pattern = re.compile(link_regex)

        for href in self.__collect_links():
            if pattern.search(href):
                return href

        for text in self.__collect_text_fragments():
            for match in re.findall(r"https?://[^\s\"'<>]+", text):
                if pattern.search(match):
                    return match

        raise AssertionError(f"Nie znaleziono linku pasującego do regex: {link_regex}")

    def __open_message_from_rows(self, *, recipient: str, subject: MailSubjectPattern) -> bool:
        rows = self.__message_rows()
        row_count = rows.count()
        for index in range(row_count):
            row = rows.nth(index)
            row_text = row.inner_text(timeout=500).strip()
            if not row_text:
                continue

            recipient_match = self.__row_contains_recipient_email(row=row, recipient=recipient)
            subject_match = self.__row_contains_subject(row=row, subject=subject)
            if recipient_match and subject_match:
                row.click()
                return True

        return False

    def __message_rows(self) -> Locator:
        if self.__provider == MailInboxProvider.ROUNDCUBE:
            row_selectors = (
                "#messagelist tbody tr",
                "table tbody tr",
                "ul li",
                ".msglist-message",
            )
        else:
            row_selectors = (
                "div.msglist-message",
                "tr.msglist-message",
                "#messages tbody tr",
                "table tbody tr",
                "ul li",
            )

        for selector in row_selectors:
            rows = self.page.locator(selector)
            if rows.count() > 0:
                return rows

        return self.page.locator("__no_such_selector__")

    @staticmethod
    def __row_contains_recipient_email(*, row: Locator, recipient: str) -> bool:
        recipient_normalized = recipient.strip().lower()
        if not recipient_normalized:
            return False

        row_text = row.inner_text(timeout=500).strip()
        row_text_normalized = row_text.lower()

        to_recipients = row.locator("div[ng-if=\"message.Content.Headers['To']\"] div.ng-binding")
        to_count = to_recipients.count()
        for index in range(to_count):
            recipient_text = to_recipients.nth(index).inner_text(timeout=300).strip().lower()
            if recipient_text == recipient_normalized:
                return True

        if InboxPage.__contains_email_token(row_text_normalized, recipient_normalized):
            return True

        emails_in_row = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", row_text)
        if any(email.lower() == recipient_normalized for email in emails_in_row):
            return True

        local_part, separator, _domain = recipient_normalized.partition("@")
        if separator and local_part:
            return InboxPage.__contains_email_token(row_text_normalized, local_part)

        return False

    @staticmethod
    def __contains_email_token(text: str, token: str) -> bool:
        escaped_token = re.escape(token)
        pattern = rf"(?<![A-Za-z0-9._%+-]){escaped_token}(?![A-Za-z0-9._%+-])"
        return bool(re.search(pattern, text))

    @staticmethod
    def __row_contains_subject(*, row: Locator, subject: MailSubjectPattern) -> bool:
        compiled_subject = subject.compiled()
        subject_locators = ("span.subject", ".subject")

        for selector in subject_locators:
            subjects = row.locator(selector)
            subject_count = subjects.count()
            for index in range(subject_count):
                subject_text = subjects.nth(index).inner_text(timeout=300).strip()
                if subject_text and compiled_subject.search(subject_text):
                    return True

        row_text = row.inner_text(timeout=500).strip()
        for line in row_text.splitlines():
            if compiled_subject.search(line.strip()):
                return True

        return False

    @staticmethod
    def __row_contains_subject_text(*, row: Locator, text: str) -> bool:
        needle = text.strip().casefold()
        if not needle:
            return False

        subject_locators = ("span.subject", ".subject")
        for selector in subject_locators:
            subjects = row.locator(selector)
            subject_count = subjects.count()
            for index in range(subject_count):
                subject_text = subjects.nth(index).inner_text(timeout=300).strip().casefold()
                if needle in subject_text:
                    return True

        row_text = row.inner_text(timeout=500).strip().casefold()
        return needle in row_text

    def __collect_links(self) -> list[str]:
        links: list[str] = []
        for container in self.__containers():
            anchors = container.locator("a[href]")
            anchor_count = anchors.count()
            for index in range(anchor_count):
                href = anchors.nth(index).get_attribute("href")
                if href:
                    links.append(href.strip())
        return links

    def __collect_text_fragments(self) -> list[str]:
        fragments: list[str] = []
        for container in self.__containers():
            body: Locator = container.locator("body")
            if body.count() == 0:
                continue
            text = body.inner_text(timeout=1_000).strip()
            if text:
                fragments.append(text)
        return fragments

    def __containers(self) -> tuple[Page | Frame, ...]:
        return (self.page, *[frame for frame in self.page.frames if frame != self.page.main_frame])
