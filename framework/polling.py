from __future__ import annotations

"""Generic polling utilities for use across all test suites.

Two primitives are provided:

- ``poll_until``  — polls an arbitrary callable until a condition is met or
  a wall-clock deadline is reached.  Uses ``time.sleep`` between probes, so
  it is suitable for backend / HTTP resources (Mailhog API, admin counters,
  OZO widget backend) where Playwright's own event-loop is not involved.

- ``HttpPoller`` — thin wrapper around ``poll_until`` that polls an HTTP
  endpoint and returns the parsed JSON payload when the condition is satisfied.
  Uses ``urllib.request`` with an unverified SSL context (same convention as
  the rest of the codebase).

Neither primitive belongs to a specific project; keep this module free of
project-level imports.
"""

import json
import ssl
import time
import urllib.request
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")

_DEFAULT_TIMEOUT_S: float = 45.0
_DEFAULT_POLL_S: float = 2.0


def poll_until(
    fn: Callable[[], _T],
    *,
    condition: Callable[[_T], bool],
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    poll_s: float = _DEFAULT_POLL_S,
    default: _T,
) -> _T:
    """Call *fn* repeatedly until ``condition(result)`` is truthy or *timeout_s* elapses.

    Returns the last value returned by *fn* regardless of whether the condition
    was satisfied — the caller is responsible for the final assertion.

    Parameters
    ----------
    fn:
        Zero-argument callable invoked on every probe.
    condition:
        Predicate applied to the result of *fn*.  Polling stops as soon as it
        returns ``True``.
    timeout_s:
        Maximum total wall-clock time in seconds.
    poll_s:
        Desired sleep duration between probes.  The actual sleep is capped to
        the remaining time so the function never overshoots the deadline.
    default:
        Returned when *fn* has not been called yet (should never happen in
        practice but keeps the return type sound).
    """
    deadline = time.monotonic() + timeout_s
    last: _T = default
    while time.monotonic() <= deadline:
        last = fn()
        if condition(last):
            return last
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(poll_s, remaining))
    return last


class HttpPoller:
    """Poll an HTTP endpoint until a JSON-payload condition is met.

    Designed for internal test-environment APIs (Mailhog, admin APIs) that
    use self-signed TLS certificates — SSL verification is intentionally
    disabled, matching the convention used elsewhere in this codebase.

    Usage::

        poller = HttpPoller(timeout_s=45, poll_s=2)
        payload = poller.poll(
            url="https://mail-galak.test.netcorner.pl/api/v2/search?...",
            condition=lambda data: data.get("total", 0) > 0,
        )
    """

    def __init__(
        self,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        poll_s: float = _DEFAULT_POLL_S,
        request_timeout_s: float = 30.0,
    ) -> None:
        self._timeout_s = timeout_s
        self._poll_s = poll_s
        self._request_timeout_s = request_timeout_s
        self._ssl_context = ssl._create_unverified_context()

    def fetch(self, url: str) -> Any:
        """Perform a single GET request and return the parsed JSON payload."""
        with urllib.request.urlopen(
            url, context=self._ssl_context, timeout=self._request_timeout_s
        ) as response:
            return json.loads(response.read().decode())

    def poll(
        self,
        url: str,
        *,
        condition: Callable[[Any], bool],
        default: Any = None,
    ) -> Any:
        """Repeatedly GET *url* until ``condition(payload)`` is truthy or timeout elapses.

        Returns the last parsed payload regardless of whether the condition
        was met — the caller owns the assertion.
        """
        return poll_until(
            fn=lambda: self.fetch(url),
            condition=condition,
            timeout_s=self._timeout_s,
            poll_s=self._poll_s,
            default=default,
        )
