from __future__ import annotations

import pytest

from framework.visual.build_metadata import build_visual_build_metadata
from framework.visual.models import VisualResult

pytestmark = [pytest.mark.aso]


def test_build_visual_build_metadata_collects_failed_visual_exclusions() -> None:
    included = VisualResult(
        scenario_id="hero",
        status="passed",
        message="ok",
        compare_mode="pixel",
        baseline_path="baseline.png",
        actual_path="actual.png",
        nodeid="qa/visual/test_home.py::test_hero[fhd]",
    )
    payloads = {
        "qa/visual/test_home.py::test_hero[fhd]": {
            "status": "passed",
            "markers": ["visual"],
        },
        "qa/visual/test_home.py::test_banner[fhd]": {
            "status": "failed",
            "markers": ["visual"],
            "pytest_outcome": {
                "phase": "setup",
                "message": "fixture setup failed: timeout",
            },
        },
        "qa/visual/test_home.py::test_skip[fhd]": {
            "status": "skipped",
            "markers": ["visual"],
            "pytest_outcome": {
                "phase": "setup",
                "message": "skipped in setup",
            },
        },
    }

    metadata = build_visual_build_metadata(results=[included], payloads_by_nodeid=payloads)

    visual = metadata["visual"]
    assert visual["collected_count"] == 3
    assert visual["included_count"] == 1
    assert visual["excluded_count"] == 1
    assert visual["excluded_cases"][0]["nodeid"] == "qa/visual/test_home.py::test_banner[fhd]"
    assert visual["excluded_cases"][0]["phase"] == "setup"
    assert visual["excluded_cases"][0]["reason_code"] == "timeout"
    assert visual["excluded_cases"][0]["reason_title"] == "Timeout during test execution"
    assert visual["excluded_cases"][0]["reason"] == "fixture setup failed: timeout"
    assert visual["excluded_cases"][0]["reason_details"] == "fixture setup failed: timeout"
    assert visual["excluded_cases"][0]["reason_raw"] == "fixture setup failed: timeout"
    assert visual["excluded_reasons_summary"] == [
        {
            "reason_code": "timeout",
            "reason_title": "Timeout during test execution",
            "count": 1,
        }
    ]


def test_build_visual_build_metadata_sanitizes_fixture_request_noise() -> None:
    payloads = {
        "qa/visual/test_home.py::test_banner[fhd]": {
            "status": "failed",
            "markers": ["visual"],
            "pytest_outcome": {
                "phase": "setup",
                "message": (
                    "request = <FixtureRequest for <Function test_banner[fhd]>>\nbrowser_context fixture failed"
                ),
            },
        },
    }

    metadata = build_visual_build_metadata(results=[], payloads_by_nodeid=payloads)

    excluded = metadata["visual"]["excluded_cases"][0]
    assert excluded["reason_code"] == "fixture_setup_error"
    assert excluded["reason_title"] == "Fixture setup error"
    assert excluded["reason"] == "browser_context fixture failed"
    assert excluded["reason_raw"].startswith("request = <FixtureRequest")
