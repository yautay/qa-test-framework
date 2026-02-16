from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import cv2


def extract_selector_from_error(longrepr: str) -> str | None:
    patterns = [
        r'locator\("(.*?)"\)',
        r"Element not found:\s*(xpath=.*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, longrepr)
        if match:
            return match.group(1).strip()
    return None


def annotate_fail_screenshot(
    raw_path: Path,
    out_path: Path,
    metadata: dict[str, str],
    highlight_box: dict[str, float] | None,
) -> None:
    image = cv2.imread(str(raw_path), cv2.IMREAD_COLOR)
    if image is None:
        return

    if highlight_box:
        x = int(highlight_box.get("x", 0))
        y = int(highlight_box.get("y", 0))
        w = int(highlight_box.get("width", 0))
        h = int(highlight_box.get("height", 0))
        if w > 0 and h > 0:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 3)

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
        cv2.putText(image, line[:180], (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(image, line[:180], (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        y += 22

    cv2.imwrite(str(out_path), image)
