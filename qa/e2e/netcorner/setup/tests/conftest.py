from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from framework.artifacts import RunArtifacts

PROMOTIONS_SERVICE_NODEID = (
    "qa/e2e/netcorner/setup/tests/test_setup_tests_promotions_service.py::"
    "test_setup_tests_promotions_service"
)
PROMO_CODES_NODEID = "qa/e2e/netcorner/setup/tests/test_setup_tests_promo_codes.py::test_setup_tests_promo_codes"
PROMOTIONS_SERVICE_DONE_FILE = "setup_promotions_service_done.timestamp"
PROMO_CODES_DELAY_SECONDS = 120
PROMO_CODES_MAX_WAIT_SECONDS = 30 * 60
PROMO_CODES_POLL_SECONDS = 1.0


def _sync_artifacts_dir(config: pytest.Config) -> Path:
    run_artifacts = getattr(config, "_run_artifacts", None)
    if run_artifacts is not None and hasattr(run_artifacts, "sync"):
        return Path(run_artifacts.sync)
    return Path(str(config.rootpath)) / ".pytest_cache"


def _promotions_service_timestamp_path(config: pytest.Config) -> Path:
    return _sync_artifacts_dir(config) / PROMOTIONS_SERVICE_DONE_FILE


def _write_promotions_service_timestamp(config: pytest.Config) -> None:
    marker_path = _promotions_service_timestamp_path(config)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(str(time.time()), encoding="utf-8")


def _wait_for_promotions_service_delay(config: pytest.Config) -> None:
    marker_path = _promotions_service_timestamp_path(config)
    deadline = time.monotonic() + PROMO_CODES_MAX_WAIT_SECONDS

    while time.monotonic() <= deadline:
        if marker_path.exists():
            raw_value = marker_path.read_text(encoding="utf-8").strip()
            try:
                finished_at = float(raw_value)
            except ValueError:
                raise pytest.UsageError(
                    "Nieprawidlowy znacznik czasu setupu promotions_service: "
                    f"{marker_path}. Oczekiwano liczby sekund UNIX."
                ) from None

            remaining = (finished_at + PROMO_CODES_DELAY_SECONDS) - time.time()
            if remaining <= 0:
                return
            time.sleep(min(PROMO_CODES_POLL_SECONDS, remaining))
            continue

        time.sleep(PROMO_CODES_POLL_SECONDS)

    raise pytest.UsageError(
        "Timeout oczekiwania na zakonczenie promotions_service przed promo_codes. "
        f"Brak znacznika: {marker_path}. "
        f"Maksymalny czas oczekiwania: {PROMO_CODES_MAX_WAIT_SECONDS}s."
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.nodeid == PROMO_CODES_NODEID:
        _wait_for_promotions_service_delay(item.config)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    result = outcome.get_result()
    setattr(item, f"rep_{result.when}", result)

    if item.nodeid == PROMOTIONS_SERVICE_NODEID and call.when == "call" and call.excinfo is None:
        _write_promotions_service_timestamp(item.config)


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
