from __future__ import annotations

import json
import time
from dataclasses import dataclass
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


@dataclass
class _SyncMarker:
    """Obsługa pliku znacznika synchronizacji promotions_service → promo_codes.

    Plik jest tworzony w katalogu per-run (opartym na run_id), aby uniknąć
    kolizji między równoległymi uruchomieniami (-n 4) i pozostałości po
    poprzednich runach w współdzielonym .pytest_cache.
    """

    path: Path

    def write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(str(time.time()), encoding="utf-8")

    def read_finished_at(self) -> float | None:
        """Zwraca znacznik czasu zakończenia lub None gdy plik nie istnieje."""
        if not self.path.exists():
            return None
        raw = self.path.read_text(encoding="utf-8").strip()
        try:
            return float(raw)
        except ValueError:
            raise pytest.UsageError(
                "Nieprawidlowy znacznik czasu setupu promotions_service: "
                f"{self.path}. Oczekiwano liczby sekund UNIX."
            ) from None

    def wait_for_delay(self, delay_s: float, max_wait_s: float, poll_s: float) -> None:
        """Blokuje do czasu aż minie `delay_s` sekund od zapisania znacznika."""
        deadline = time.monotonic() + max_wait_s
        while time.monotonic() <= deadline:
            finished_at = self.read_finished_at()
            if finished_at is not None:
                remaining = (finished_at + delay_s) - time.time()
                if remaining <= 0:
                    return
                time.sleep(min(poll_s, remaining))
                continue
            time.sleep(poll_s)

        raise pytest.UsageError(
            "Timeout oczekiwania na zakonczenie promotions_service przed promo_codes. "
            f"Brak znacznika: {self.path}. "
            f"Maksymalny czas oczekiwania: {max_wait_s}s."
        )


def _build_sync_marker(config: pytest.Config) -> _SyncMarker:
    """Buduje _SyncMarker z ścieżką w katalogu per-run (run_artifacts.root lub .pytest_cache)."""
    run_artifacts = getattr(config, "_run_artifacts", None)
    if run_artifacts is not None and hasattr(run_artifacts, "root"):
        base = Path(run_artifacts.root)
    else:
        # Fallback: unikaj kolizji między runami — użyj run_id z env lub rootpath.
        import os
        run_id = os.getenv("PYTEST_XDIST_TESTRUNUID", "").strip()
        if run_id:
            base = Path(str(config.rootpath)) / ".pytest_cache" / run_id
        else:
            base = Path(str(config.rootpath)) / ".pytest_cache"
    return _SyncMarker(path=base / PROMOTIONS_SERVICE_DONE_FILE)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.nodeid == PROMO_CODES_NODEID:
        marker = _build_sync_marker(item.config)
        marker.wait_for_delay(
            delay_s=PROMO_CODES_DELAY_SECONDS,
            max_wait_s=PROMO_CODES_MAX_WAIT_SECONDS,
            poll_s=PROMO_CODES_POLL_SECONDS,
        )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    result = outcome.get_result()
    setattr(item, f"rep_{result.when}", result)

    if item.nodeid == PROMOTIONS_SERVICE_NODEID and call.when == "call" and call.excinfo is None:
        _build_sync_marker(item.config).write()


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
