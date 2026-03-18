from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np
import pytest

import framework.visual.compare_pixel as compare_pixel
from framework.visual.compare_pixel import compare_images

pytestmark = [pytest.mark.aso]


def _make_image(path: Path) -> np.ndarray:
    image = np.zeros((80, 120, 3), dtype=np.uint8)
    cv2.rectangle(image, (20, 15), (100, 65), (255, 255, 255), thickness=cv2.FILLED)
    cv2.circle(image, (60, 40), 10, (0, 128, 255), thickness=cv2.FILLED)
    cv2.imwrite(str(path), image)
    return image


def _shifted_down(image: np.ndarray, dy: int, path: Path) -> None:
    h, w = image.shape[:2]
    shifted = np.zeros((h, w, 3), dtype=np.uint8)
    shifted[dy:, :] = image[: h - dy, :]
    cv2.imwrite(str(path), shifted)


def test_compare_images_reduces_false_diff_when_shift_compensation_enabled(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.png"
    actual_path = tmp_path / "actual.png"
    diff_no_shift = tmp_path / "diff-no-shift.png"
    diff_shift = tmp_path / "diff-shift.png"

    baseline = _make_image(baseline_path)
    _shifted_down(baseline, 4, actual_path)

    without_comp = compare_images(
        baseline_path,
        actual_path,
        diff_no_shift,
        diff_threshold=1,
        blur_ksize=0,
        min_region_area=1,
        dilate_iters=0,
        shift_compensation_y_px=0,
        return_details=True,
    )
    with_comp = compare_images(
        baseline_path,
        actual_path,
        diff_shift,
        diff_threshold=1,
        blur_ksize=0,
        min_region_area=1,
        dilate_iters=0,
        shift_compensation_y_px=6,
        return_details=True,
    )
    without_comp = cast(dict[str, Any], without_comp)
    with_comp = cast(dict[str, Any], with_comp)

    assert float(without_comp["changed_ratio"]) > 0.0
    assert float(with_comp["changed_ratio"]) < float(without_comp["changed_ratio"])
    assert abs(int(with_comp["applied_shift_y"])) == 4


def test_compare_images_keeps_shift_zero_when_compensation_disabled(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.png"
    actual_path = tmp_path / "actual.png"
    diff_path = tmp_path / "diff.png"

    baseline = _make_image(baseline_path)
    _shifted_down(baseline, 3, actual_path)

    details = compare_images(
        baseline_path,
        actual_path,
        diff_path,
        shift_compensation_y_px=0,
        return_details=True,
    )
    details = cast(dict[str, Any], details)

    assert int(details["applied_shift_y"]) == 0
    assert int(details["shift_compensation_y_px"]) == 0


def test_find_best_vertical_shift_returns_zero_for_tiny_gain(monkeypatch: pytest.MonkeyPatch) -> None:
    baseline = np.zeros((200, 16, 3), dtype=np.uint8)
    actual = np.zeros_like(baseline)

    def _fake_err(_baseline: np.ndarray, _actual: np.ndarray, dy: int) -> float:
        if dy == 0:
            return 10.0
        if dy == 100:
            return 9.7
        if abs(dy) <= 20:
            return 9.75
        return 9.71

    monkeypatch.setattr(compare_pixel, "_alignment_error_for_shift", _fake_err)

    applied = compare_pixel._find_best_vertical_shift(baseline, actual, 100)
    assert applied == 0


def test_find_best_vertical_shift_avoids_boundary_escape(monkeypatch: pytest.MonkeyPatch) -> None:
    baseline = np.zeros((200, 16, 3), dtype=np.uint8)
    actual = np.zeros_like(baseline)

    def _fake_err(_baseline: np.ndarray, _actual: np.ndarray, dy: int) -> float:
        if dy == 0:
            return 10.0
        if dy == 7:
            return 8.0
        if dy == 100:
            return 7.95
        if abs(dy) <= 20:
            return 8.3
        return 8.1

    monkeypatch.setattr(compare_pixel, "_alignment_error_for_shift", _fake_err)

    applied = compare_pixel._find_best_vertical_shift(baseline, actual, 100)
    assert applied == 7
