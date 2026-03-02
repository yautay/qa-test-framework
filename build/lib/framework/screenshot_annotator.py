from __future__ import annotations

"""Utilities that enrich failure screenshots with highlights and metadata text."""

import re
from datetime import UTC, datetime
from pathlib import Path

import cv2


def extract_selector_from_error(longrepr: str) -> str | None:
    """Try to parse the locator or xpath string from a Playwright failure message."""
    patterns = [
        # locator("...") or locator('...')
        r'locator\((?:"([^"]*)"|\'([^\']*)\')\)',
        # keep only one line after "Element not found:"
        r"Element not found:\s*(xpath=[^\n\r]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, longrepr, flags=re.MULTILINE)
        if match:
            # first non-empty group
            for g in match.groups():
                if g:
                    return g.strip()
    return None


def annotate_fail_screenshot(
        raw_path: Path,
        out_path: Path,
        metadata: dict[str, str],
        highlight_box: dict[str, float] | None,
) -> None:
    """Draw a highlight box and overlay metadata text onto the failure capture."""
    image = cv2.imread(str(raw_path), cv2.IMREAD_COLOR)
    if image is None:
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)

    h_img, w_img = image.shape[:2]

    if isinstance(highlight_box, dict) and highlight_box:
        x = int(highlight_box.get("x", 0))
        y = int(highlight_box.get("y", 0))
        w = int(highlight_box.get("width", 0))
        h = int(highlight_box.get("height", 0))

        if w > 0 and h > 0:
            # clamp to image boundaries
            x1 = max(0, min(w_img - 1, x))
            y1 = max(0, min(h_img - 1, y))
            x2 = max(0, min(w_img - 1, x + w))
            y2 = max(0, min(h_img - 1, y + h))
            if x2 > x1 and y2 > y1:
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)

    lines = [
        "status=FAIL",
        f"time={datetime.now(UTC).isoformat()}",
        f"nodeid={metadata.get('nodeid', '-')}",
        f"branch={metadata.get('branch', '-')}",
        f"commit={metadata.get('commit', '-')}",
        f"user={metadata.get('user', '-')}",
    ]

    y = 26
    for line in lines:
        text = line[:180]
        cv2.putText(image, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(image, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        y += 22

    ok = cv2.imwrite(str(out_path), image)
    if not ok:
        # Silent failure is often annoying; raising is a design choice.
        # Here we choose to fail silently like the original, but you could log/raise.
        return
