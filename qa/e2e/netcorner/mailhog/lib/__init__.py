"""Shared mail inbox support for Netcorner tests."""

from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService
from qa.e2e.netcorner.mailhog.lib.mail_subjects import MailSubjectPattern, MailSubjects

__all__ = ["MailInboxService", "MailSubjectPattern", "MailSubjects"]
