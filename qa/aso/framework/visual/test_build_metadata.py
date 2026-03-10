from __future__ import annotations

from framework.visual.build_metadata import build_visual_build_metadata
from framework.visual.models import VisualResult


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
    assert visual["excluded_cases"][0]["reason"] == "fixture setup failed: timeout"
