from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework.visual.scenario_loader import (
    ScenarioLoadError,
    _load_scenarios,
    format_load_errors,
    load_scenarios_with_errors,
)

pytestmark = [pytest.mark.aso]


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _base_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "scenario-1",
        "suite_id": "suite-1",
        "target_url": "https://example.test/",
    }
    payload.update(overrides)
    return payload


def test_load_scenarios_single_object_defaults(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.json"
    payload = {
        "suite_id": "suite-1",
        "target_url": "https://example.test/",
        "viewport": ["1280", "720"],
    }
    _write_json(file_path, payload)

    scenarios = _load_scenarios(file_path)

    assert len(scenarios) == 1
    scenario = scenarios[0]
    assert scenario.scenario_id == "sample__1"
    assert scenario.name == "sample__1"
    assert scenario.compare_mode == "hybrid"
    assert scenario.viewport == ["1280", "720"]
    assert scenario.capture.capture_type == "page"
    assert scenario.capture.selector == ""
    assert scenario.capture.full_page is True
    assert scenario.thresholds.pixel_max == 0.005
    assert scenario.thresholds.lpips_max == 0.08
    assert scenario.thresholds.dists_max == 0.08
    assert scenario.mask.selectors == ()
    assert scenario.mask.color == "#00FF00"
    assert scenario.steps == ()
    assert scenario.perceptual_required is False


def test_load_scenarios_supports_list_and_container(tmp_path: Path) -> None:
    list_path = tmp_path / "list.json"
    _write_json(
        list_path,
        [
            _base_payload(id="scenario-a"),
            _base_payload(id="scenario-b", name="Scenario B"),
        ],
    )

    dict_path = tmp_path / "container.json"
    _write_json(
        dict_path,
        {
            "scenarios": [
                _base_payload(id="scenario-c"),
                _base_payload(id="scenario-d"),
            ]
        },
    )

    list_scenarios = _load_scenarios(list_path)
    dict_scenarios = _load_scenarios(dict_path)

    assert [s.scenario_id for s in list_scenarios] == ["scenario-a", "scenario-b"]
    assert [s.scenario_id for s in dict_scenarios] == ["scenario-c", "scenario-d"]


def test_load_scenarios_parses_steps_and_thresholds(tmp_path: Path) -> None:
    file_path = tmp_path / "steps.json"
    _write_json(
        file_path,
        _base_payload(
            compare_mode="Perceptual",
            capture={"type": "element", "selector": "#hero", "full_page": False},
            thresholds={"pixel_max": "0.01", "lpips_max": 0.12, "dists_max": "0.2"},
            mask={"selectors": [".badge"], "color": "#123456"},
            steps=[
                {
                    "action": "  click ",
                    "selector": "#cta",
                    "value": "ok",
                    "timeout_ms": "1500",
                    "url": " https://example.test/step ",
                }
            ],
            perceptual_required=True,
        ),
    )

    scenario = _load_scenarios(file_path)[0]

    assert scenario.compare_mode == "perceptual"
    assert scenario.capture.capture_type == "element"
    assert scenario.capture.selector == "#hero"
    assert scenario.capture.full_page is False
    assert scenario.thresholds.pixel_max == 0.01
    assert scenario.thresholds.lpips_max == 0.12
    assert scenario.thresholds.dists_max == 0.2
    assert scenario.mask.selectors == (".badge",)
    assert scenario.mask.color == "#123456"
    assert scenario.steps[0].action == "click"
    assert scenario.steps[0].selector == "#cta"
    assert scenario.steps[0].value == "ok"
    assert scenario.steps[0].timeout_ms == 1500
    assert scenario.steps[0].url == "https://example.test/step"
    assert scenario.perceptual_required is True


def test_load_scenarios_rejects_invalid_top_level(tmp_path: Path) -> None:
    file_path = tmp_path / "invalid.json"
    _write_json(file_path, ["not-a-dict"])

    with pytest.raises(ValueError, match="top-level JSON must be"):
        _load_scenarios(file_path)


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"compare_mode": "side-by-side"}, "compare_mode must be"),
        ({"capture": ["x"]}, "capture must be an object"),
        ({"capture": {"type": "zoom"}}, "capture.type must be"),
        ({"capture": {"full_page": "yes"}}, "capture.full_page must be a boolean"),
        ({"mask": ["x"]}, "mask must be an object"),
        ({"mask": {"selectors": [".ok", 1]}}, "mask.selectors must be a list of strings"),
        ({"thresholds": ["x"]}, "thresholds must be an object"),
        ({"thresholds": {"pixel_max": "nope"}}, "thresholds.pixel_max must be a number"),
        ({"steps": "do it"}, "steps must be a list of objects"),
        ({"steps": ["click"]}, "steps must be a list of objects"),
        ({"steps": [{"timeout_ms": "1s"}]}, r"steps\[0\]\.timeout_ms must be an int"),
    ],
)
def test_load_scenarios_rejects_invalid_fields(tmp_path: Path, overrides: dict[str, object], match: str) -> None:
    file_path = tmp_path / "invalid_fields.json"
    _write_json(file_path, _base_payload(**overrides))

    with pytest.raises(ValueError, match=match):
        _load_scenarios(file_path)


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"suite_id": ""}, "suite_id must be non-empty"),
        ({"target_url": ""}, "target_url must be non-empty"),
        ({"id": "   "}, "id must be non-empty"),
    ],
)
def test_load_scenarios_requires_non_empty_fields(tmp_path: Path, overrides: dict[str, object], match: str) -> None:
    file_path = tmp_path / "missing.json"
    _write_json(file_path, _base_payload(**overrides))

    with pytest.raises(ValueError, match=match):
        _load_scenarios(file_path)


def test_load_scenarios_with_errors_collects_failures_and_duplicates(tmp_path: Path) -> None:
    valid_one = tmp_path / "valid_one.json"
    valid_two = tmp_path / "valid_two.json"
    invalid = tmp_path / "invalid.json"

    _write_json(valid_one, _base_payload(id="dup"))
    _write_json(valid_two, _base_payload(id="dup", name="Second"))
    invalid.write_text("{not-json", encoding="utf-8")

    scenarios, errors = load_scenarios_with_errors(tmp_path)

    assert [s.scenario_id for s in scenarios] == ["dup", "dup"]
    assert len(errors) == 2
    assert any("invalid JSON" in error.message for error in errors)
    assert any("Duplicate scenario id" in error.message for error in errors)


def test_format_load_errors() -> None:
    errors = [
        ScenarioLoadError(file=Path("a.json"), message="boom"),
        ScenarioLoadError(file=Path("b.json"), message="nope"),
    ]

    formatted = format_load_errors(errors)

    assert formatted == "Visual scenario load errors:\n- a.json: boom\n- b.json: nope"


def test_load_scenarios_empty_lists_are_treated_as_missing_sections(tmp_path: Path) -> None:
    file_path = tmp_path / "empty_sections.json"
    _write_json(
        file_path,
        _base_payload(
            capture=[],
            mask=[],
            thresholds=[],
        ),
    )

    scenario = _load_scenarios(file_path)[0]

    assert scenario.capture.capture_type == "page"
    assert scenario.mask.selectors == ()
    assert scenario.thresholds.pixel_max == 0.005
