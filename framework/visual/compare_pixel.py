from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


_COARSE_SHIFT_SPAN_PX = 20
_SHIFT_PENALTY_LAMBDA = 10.0
_MIN_SHIFT_IMPROVEMENT = 0.5
_BOUNDARY_MARGIN_IMPROVEMENT = 1.0


def _vertical_shifted(image: np.ndarray, dy: int) -> tuple[np.ndarray, np.ndarray]:
    h, w = image.shape[:2]
    shifted = np.zeros_like(image)
    valid = np.zeros((h, w), dtype=np.uint8)
    if dy > 0:
        if dy < h:
            shifted[dy:, :] = image[: h - dy, :]
            valid[dy:, :] = 255
        return shifted, valid
    if dy < 0:
        d = -dy
        if d < h:
            shifted[: h - d, :] = image[d:, :]
            valid[: h - d, :] = 255
        return shifted, valid
    shifted[:, :] = image
    valid[:, :] = 255
    return shifted, valid


def _alignment_error_for_shift(baseline: np.ndarray, actual: np.ndarray, dy: int) -> float:
    h = int(baseline.shape[0])
    if dy > 0:
        if dy >= h:
            return float("inf")
        b = baseline[dy:, :]
        a = actual[: h - dy, :]
    elif dy < 0:
        d = -dy
        if d >= h:
            return float("inf")
        b = baseline[: h - d, :]
        a = actual[d:, :]
    else:
        b = baseline
        a = actual

    if b.size == 0 or a.size == 0:
        return float("inf")

    diff = cv2.absdiff(b, a)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def _find_best_vertical_shift(baseline: np.ndarray, actual: np.ndarray, max_shift: int) -> int:
    span = max(0, int(max_shift))
    if span <= 0:
        return 0

    h = max(1, int(baseline.shape[0]))

    def _score_for_shift(dy: int) -> tuple[float, float]:
        err = _alignment_error_for_shift(baseline, actual, dy)
        if not np.isfinite(err):
            return float("inf"), float("inf")
        shift_penalty = _SHIFT_PENALTY_LAMBDA * (abs(int(dy)) / float(h))
        return float(err + shift_penalty), float(err)

    def _best_shift_in_span(local_span: int) -> tuple[int, float, float]:
        best_local_dy = 0
        best_local_score, best_local_err = _score_for_shift(0)
        for local_dy in range(-local_span, local_span + 1):
            score, err = _score_for_shift(local_dy)
            if score < best_local_score:
                best_local_score = score
                best_local_err = err
                best_local_dy = local_dy
        return int(best_local_dy), float(best_local_score), float(best_local_err)

    _, _, err0 = _best_shift_in_span(0)
    coarse_span = min(span, _COARSE_SHIFT_SPAN_PX)
    coarse_dy, _, coarse_err = _best_shift_in_span(coarse_span)
    coarse_improvement = err0 - coarse_err

    if span == coarse_span:
        return int(coarse_dy) if coarse_improvement >= _MIN_SHIFT_IMPROVEMENT else 0

    if coarse_improvement < _MIN_SHIFT_IMPROVEMENT:
        return 0

    full_dy, _, full_err = _best_shift_in_span(span)
    full_improvement = err0 - full_err
    if full_improvement < _MIN_SHIFT_IMPROVEMENT:
        return 0

    if abs(full_dy) == span:
        boundary_gain_over_coarse = coarse_err - full_err
        if boundary_gain_over_coarse < _BOUNDARY_MARGIN_IMPROVEMENT:
            return int(coarse_dy)

    return int(full_dy)


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
    shift_compensation_y_px: int = 0,
    return_details: bool = False,
) -> float | tuple[float, int] | dict[str, float | int]:
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
        if return_details:
            return {
                "changed_ratio": 1.0,
                "bbox_count": 0,
                "applied_shift_y": 0,
                "shift_compensation_y_px": max(0, int(shift_compensation_y_px)),
            }
        return (1.0, 0) if return_bbox_count else 1.0

    if baseline.shape != actual.shape:
        actual = cv2.resize(actual, (baseline.shape[1], baseline.shape[0]), interpolation=cv2.INTER_AREA)

    shift_span = max(0, int(shift_compensation_y_px))
    applied_shift_y = _find_best_vertical_shift(baseline, actual, shift_span) if shift_span > 0 else 0
    aligned_actual, valid_region = _vertical_shifted(actual, applied_shift_y)

    abs_diff = cv2.absdiff(baseline, aligned_actual)
    gray = cv2.cvtColor(abs_diff, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_and(gray, valid_region)

    # 1) reduce tiny pixel noise
    if blur_ksize and blur_ksize > 0:
        k = blur_ksize if blur_ksize % 2 == 1 else blur_ksize + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)
        gray = cv2.bitwise_and(gray, valid_region)

    # 2) threshold meaningful differences
    t = max(0, min(255, int(diff_threshold)))
    _, binary = cv2.threshold(gray, t, 255, cv2.THRESH_BINARY)

    # 3) morphology: remove speckles + merge close pixels
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    if dilate_iters and dilate_iters > 0:
        binary = cv2.dilate(binary, kernel, iterations=int(dilate_iters))

    binary = cv2.bitwise_and(binary, valid_region)

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
    total = int(np.count_nonzero(valid_region))
    changed_ratio = changed / total if total else 1.0

    # 5) build a readable overlay + bounding boxes
    overlay = aligned_actual.copy()
    red = np.zeros_like(actual)
    red[:] = (0, 0, 255)

    sel = mask > 0
    if np.any(sel):
        a = aligned_actual[sel].astype(np.float32)
        r = red[sel].astype(np.float32)
        out = a * 0.35 + r * 0.65
        overlay[sel] = np.clip(out, 0, 255).astype(np.uint8)

    # for x, y, w, h in kept_boxes:
    #     cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)

    diff_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(diff_path), overlay)

    if return_details:
        return {
            "changed_ratio": float(changed_ratio),
            "bbox_count": int(len(kept_boxes)),
            "applied_shift_y": int(applied_shift_y),
            "shift_compensation_y_px": int(shift_span),
        }
    if return_bbox_count:
        return changed_ratio, len(kept_boxes)
    return changed_ratio
