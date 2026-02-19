from __future__ import annotations

import pytest

from framework.visual.models import VisualThresholds

pytestmark = [pytest.mark.aso]


class TestVisualThresholdsUncertainDeltas:
    def test_with_all_uncertain_deltas(self):
        t = VisualThresholds(
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
            pixel_uncertain_delta=0.002,
            lpips_uncertain_delta=0.015,
            dists_uncertain_delta=0.01,
        )
        assert t.pixel_uncertain_delta == 0.002
        assert t.lpips_uncertain_delta == 0.015
        assert t.dists_uncertain_delta == 0.01

    def test_without_uncertain_deltas_defaults_to_none(self):
        t = VisualThresholds(
            pixel_max=0.005,
            lpips_max=0.08,
            dists_max=0.08,
        )
        assert t.pixel_uncertain_delta is None
        assert t.lpips_uncertain_delta is None
        assert t.dists_uncertain_delta is None


class TestVisualThresholdsFromDict:
    def test_with_uncertain_deltas(self):
        d = {
            "pixel_max": 0.005,
            "lpips_max": 0.08,
            "dists_max": 0.08,
            "pixel_uncertain_delta": 0.003,
            "lpips_uncertain_delta": 0.015,
        }
        t = VisualThresholds.from_dict(d)
        assert t.pixel_uncertain_delta == 0.003
        assert t.lpips_uncertain_delta == 0.015
        assert t.dists_uncertain_delta is None

    def test_without_uncertain_deltas(self):
        d = {
            "pixel_max": 0.005,
            "lpips_max": 0.08,
        }
        t = VisualThresholds.from_dict(d)
        assert t.pixel_uncertain_delta is None
        assert t.lpips_uncertain_delta is None
