from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from framework.visual.baseline_store import BaselineStore
from framework.reporting.report_server.context import ReportServerContext
from qa.aso.framework.visual.report_server_http_test_helpers import _env, _http_json, _start_server, _stop_server

pytestmark = [pytest.mark.aso]


def test_perceptual_queue_endpoint_reports_disabled_when_not_configured(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    ui_dist = tmp_path / "ui-dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html>ui</html>", encoding="utf-8")

    context = ReportServerContext(
        repo_root=repo_root,
        ui_dist_dir=ui_dist,
        baseline_store=BaselineStore(cast(Any, _env()), repo_root),
        run_dirs={},
        pms_enabled=False,
    )

    server, base_url, thread = _start_server(context)
    try:
        status, payload = _http_json(base_url, "/api/perceptual/queue")
        assert status == 200
        assert payload["enabled"] is False
        assert payload["server_active"] == 0
        assert payload["queued"] == 0
        assert payload["running"] == 0
    finally:
        _stop_server(server, thread)
