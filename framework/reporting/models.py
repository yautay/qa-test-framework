from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AsyncReportingEvent:
    """One reporting event tracked by the async worker."""

    kind: str
    payload: dict[str, Any]
    priority: int
    sequence: int
    created_at_monotonic: float
    attempt: int = 1
    next_attempt_at_monotonic: float = 0.0


@dataclass(slots=True)
class AsyncReportingStats:
    """Aggregated async queue counters emitted at shutdown."""

    queued: int = 0
    sent: int = 0
    failed: int = 0
    retried: int = 0
    dropped: int = 0
    expired: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "queued": int(self.queued),
            "sent": int(self.sent),
            "failed": int(self.failed),
            "retried": int(self.retried),
            "dropped": int(self.dropped),
            "expired": int(self.expired),
        }
