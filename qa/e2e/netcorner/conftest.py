from __future__ import annotations

import pytest

from framework.env import RuntimeEnv
from qa.e2e.netcorner.mailhog.lib.flows.inbox_flow import MailInboxService


@pytest.fixture(scope="function")
def mail_inbox(runtime_env: RuntimeEnv) -> MailInboxService:
    return MailInboxService(runtime_env)
