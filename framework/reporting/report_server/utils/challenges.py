from __future__ import annotations

import time

from ..context import ReportServerContext


def _cleanup_expired_challenges(context: ReportServerContext) -> None:
    now = time.time()
    with context._lock:
        expired = [challenge_id for challenge_id, item in context.challenges.items() if item.expires_at <= now]
        for challenge_id in expired:
            context.challenges.pop(challenge_id, None)


def _generate_phrase() -> str:
    adjectives = ["amber", "calm", "delta", "frozen", "gentle", "rapid", "silent", "solar"]
    nouns = ["anchor", "bridge", "cloud", "forest", "harbor", "river", "signal", "valley"]
    idx = int(time.time() * 1000) % 100
    return f"{adjectives[idx % len(adjectives)]}-{nouns[(idx // 2) % len(nouns)]}-{idx:02d}"
