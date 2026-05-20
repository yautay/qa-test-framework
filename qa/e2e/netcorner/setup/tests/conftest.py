from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from framework.artifacts import RunArtifacts


def pytest_configure(config: pytest.Config) -> None:
    numprocesses = getattr(config.option, "numprocesses", None)
    try:
        workers = int(numprocesses or 0)
    except (TypeError, ValueError):
        workers = 0

    if workers > 1:
        raise pytest.UsageError(
            "Setup suite qa/e2e/netcorner/setup/tests musi dzialac szeregowo. "
            "Uruchom bez xdist albo z -n 1."
        )


@pytest.fixture(scope="function")
def setup_action_logger(request: pytest.FixtureRequest, run_artifacts: RunArtifacts):
    log_dir = Path(run_artifacts.logs) / "setup"
    log_dir.mkdir(parents=True, exist_ok=True)

    nodeid_safe = request.node.nodeid.replace("::", "__").replace("/", "_")
    log_path = log_dir / f"{nodeid_safe}.log"

    def _write(action: str, params: dict[str, object]) -> None:
        payload = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "test": request.node.nodeid,
            "action": action,
            "params": params,
        }
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    _write("test_start", {})
    yield _write
    status = "passed"
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call is not None and rep_call.failed:
        status = "failed"
    _write("test_finish", {"status": status, "log_file": str(log_path)})
