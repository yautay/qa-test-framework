from __future__ import annotations

import pytest
from playwright.sync_api import Page

from framework.env import RuntimeEnv
from qa.e2e.netcorner.admin.lib.flows.admin_wrappers import AdminWrappers
from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService


@pytest.fixture(scope="function")
def mail_inbox(runtime_env: RuntimeEnv) -> MailInboxService:
    return MailInboxService(runtime_env)


@pytest.fixture(scope="function")
def admin_panel(page: Page, runtime_env: RuntimeEnv) -> AdminWrappers:
    """Provides an AdminWrappers instance bound to the current test page.

    The wrapper does NOT open the admin panel automatically — call
    ``admin_panel.open_admin()`` explicitly in your test or fixture when needed.
    This avoids unnecessary admin navigation in tests that only need the wrapper
    for teardown/setup purposes.
    """
    return AdminWrappers(page, runtime_env)
