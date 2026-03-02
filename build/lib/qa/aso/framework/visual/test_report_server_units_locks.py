from __future__ import annotations

from pathlib import Path

import pytest

from framework.visual.report_server import LOCK_TTL_SECONDS, _acquire_lock

pytestmark = [pytest.mark.aso]


class TestLocks:
    def test_acquire_lock_denies_active_lock(self, tmp_path: Path) -> None:
        build_dir = tmp_path / "artifacts" / "run-1"
        build_dir.mkdir(parents=True)

        first = _acquire_lock(build_dir, "client-a", now=1000.0)
        assert first["accepted"] is True

        second = _acquire_lock(build_dir, "client-b", now=1000.0 + LOCK_TTL_SECONDS - 1)
        assert second["accepted"] is False
        assert second["reason"] == "locked"

    def test_acquire_lock_allows_takeover_after_expiry(self, tmp_path: Path) -> None:
        build_dir = tmp_path / "artifacts" / "run-2"
        build_dir.mkdir(parents=True)

        first = _acquire_lock(build_dir, "client-a", now=2000.0)
        assert first["accepted"] is True

        second = _acquire_lock(build_dir, "client-b", now=2000.0 + LOCK_TTL_SECONDS + 1)
        assert second["accepted"] is True
        assert second["lock"]["owner_client_id"] == "client-b"
