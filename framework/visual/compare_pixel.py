from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def compare_images(baseline_path: Path, actual_path: Path, diff_path: Path) -> float:
    baseline = cv2.imread(str(baseline_path), cv2.IMREAD_COLOR)
    actual = cv2.imread(str(actual_path), cv2.IMREAD_COLOR)
    if baseline is None or actual is None:
        return 1.0

    if baseline.shape != actual.shape:
        actual = cv2.resize(actual, (baseline.shape[1], baseline.shape[0]),
                            interpolation=cv2.INTER_AREA)

    abs_diff = cv2.absdiff(baseline, actual)
    gray = cv2.cvtColor(abs_diff, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)

    changed = int(np.count_nonzero(binary))
    total = int(binary.shape[0] * binary.shape[1])
    changed_ratio = changed / total if total else 1.0

    overlay = actual.copy()
    overlay[binary > 0] = (0, 0, 255)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(diff_path), overlay)
    return changed_ratio
