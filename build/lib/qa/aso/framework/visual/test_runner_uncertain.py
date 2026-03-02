from __future__ import annotations

import pytest

from framework.visual.runner import _evaluate

pytestmark = [pytest.mark.aso]


class TestUncertainPixelZone:
    def test_uncertain_when_pixel_in_zone(self):
        status, msg = _evaluate(
            mode="pixel",
            pixel_changed_ratio=0.0055,
            lpips=None,
            dists=None,
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            uncertain_enabled=True,
            pixel_uncertain_delta=0.001,
            lpips_uncertain_delta=0.01,
            dists_uncertain_delta=0.01,
        )
        assert status == "uncertain"
        assert "uncertainty" in msg.lower()

    def test_passed_when_pixel_below_threshold(self):
        status, msg = _evaluate(
            mode="pixel",
            pixel_changed_ratio=0.004,
            lpips=None,
            dists=None,
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            uncertain_enabled=True,
            pixel_uncertain_delta=0.001,
            lpips_uncertain_delta=0.01,
            dists_uncertain_delta=0.01,
        )
        assert status == "passed"

    def test_failed_when_pixel_above_uncertain_zone(self):
        status, msg = _evaluate(
            mode="pixel",
            pixel_changed_ratio=0.007,
            lpips=None,
            dists=None,
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            uncertain_enabled=True,
            pixel_uncertain_delta=0.001,
            lpips_uncertain_delta=0.01,
            dists_uncertain_delta=0.01,
        )
        assert status == "failed"


class TestUncertainDisabled:
    def test_failed_when_uncertain_disabled(self):
        status, msg = _evaluate(
            mode="pixel",
            pixel_changed_ratio=0.0055,
            lpips=None,
            dists=None,
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            uncertain_enabled=False,
            pixel_uncertain_delta=0.001,
            lpips_uncertain_delta=0.01,
            dists_uncertain_delta=0.01,
        )
        assert status == "failed"


class TestUncertainHybrid:
    def test_uncertain_when_perceptual_ok_pixel_in_zone(self):
        status, msg = _evaluate(
            mode="hybrid",
            pixel_changed_ratio=0.0055,
            lpips=0.05,
            dists=0.05,
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            uncertain_enabled=True,
            pixel_uncertain_delta=0.001,
            lpips_uncertain_delta=0.01,
            dists_uncertain_delta=0.01,
        )
        assert status == "uncertain"

    def test_uncertain_when_perceptual_ok_pixel_exceeded(self):
        status, msg = _evaluate(
            mode="hybrid",
            pixel_changed_ratio=0.01,
            lpips=0.05,
            dists=0.05,
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            uncertain_enabled=True,
            pixel_uncertain_delta=0.001,
            lpips_uncertain_delta=0.01,
            dists_uncertain_delta=0.01,
        )
        assert status == "uncertain"

    def test_passed_when_all_ok(self):
        status, msg = _evaluate(
            mode="hybrid",
            pixel_changed_ratio=0.003,
            lpips=0.05,
            dists=0.05,
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            uncertain_enabled=True,
            pixel_uncertain_delta=0.001,
            lpips_uncertain_delta=0.01,
            dists_uncertain_delta=0.01,
        )
        assert status == "passed"
