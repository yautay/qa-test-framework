from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def compare_images(
    baseline_path: Path,
    actual_path: Path,
    diff_path: Path,
    *,
    diff_threshold: int = 30,
    blur_ksize: int = 10,
    min_region_area: int = 40,
    dilate_iters: int = 1,
    return_bbox_count: bool = False,
) -> float | tuple[float, int]:
    """Practical pixel diff:
    - thresholds per-pixel delta
    - reduces noise (blur + morphology)
    - ignores tiny regions
    - writes an overlay diff image

    Returns changed_ratio (and optionally number of diff regions).
    """
    baseline = cv2.imread(str(baseline_path), cv2.IMREAD_COLOR)
    actual = cv2.imread(str(actual_path), cv2.IMREAD_COLOR)
    if baseline is None or actual is None:
        return (1.0, 0) if return_bbox_count else 1.0

    if baseline.shape != actual.shape:
        actual = cv2.resize(actual, (baseline.shape[1], baseline.shape[0]), interpolation=cv2.INTER_AREA)

    abs_diff = cv2.absdiff(baseline, actual)
    gray = cv2.cvtColor(abs_diff, cv2.COLOR_BGR2GRAY)

    # 1) reduce tiny pixel noise
    if blur_ksize and blur_ksize > 0:
        k = blur_ksize if blur_ksize % 2 == 1 else blur_ksize + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)

    # 2) threshold meaningful differences
    t = max(0, min(255, int(diff_threshold)))
    _, binary = cv2.threshold(gray, t, 255, cv2.THRESH_BINARY)

    # 3) morphology: remove speckles + merge close pixels
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    if dilate_iters and dilate_iters > 0:
        binary = cv2.dilate(binary, kernel, iterations=int(dilate_iters))

    # 4) find regions and ignore tiny ones
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    mask = np.zeros_like(binary)
    kept_boxes: list[tuple[int, int, int, int]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < float(min_region_area):
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        kept_boxes.append((x, y, w, h))
        cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)

    # ratio computed on filtered mask (more stable)
    changed = int(np.count_nonzero(mask))
    total = int(mask.shape[0] * mask.shape[1])
    changed_ratio = changed / total if total else 1.0

    # 5) build a readable overlay + bounding boxes
    overlay = actual.copy()
    red = np.zeros_like(actual)
    red[:] = (0, 0, 255)

    sel = mask > 0
    if np.any(sel):
        a = actual[sel].astype(np.float32)
        r = red[sel].astype(np.float32)
        out = a * 0.35 + r * 0.65
        overlay[sel] = np.clip(out, 0, 255).astype(np.uint8)

    # for x, y, w, h in kept_boxes:
    #     cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)

    diff_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(diff_path), overlay)

    if return_bbox_count:
        return changed_ratio, len(kept_boxes)
    return changed_ratio
