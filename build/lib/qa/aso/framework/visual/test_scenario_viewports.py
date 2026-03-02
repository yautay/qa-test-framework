from __future__ import annotations

import json
from pathlib import Path

import pytest

from framework.visual.scenario_loader import _load_scenarios

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


def test_load_scenarios_accepts_viewport_string(tmp_path: Path) -> None:
    file_path = tmp_path / "viewport_string.json"
    _write_json(file_path, _base_payload(viewport="fhd"))

    scenario = _load_scenarios(file_path)[0]

    assert scenario.viewport == ("fhd",)


def test_load_scenarios_accepts_viewport_list(tmp_path: Path) -> None:
    file_path = tmp_path / "viewport_list.json"
    _write_json(file_path, _base_payload(viewport=["fhd", "2k"]))

    scenario = _load_scenarios(file_path)[0]

    assert scenario.viewport == ("fhd", "2k")


def test_load_scenarios_default_viewport_is_empty(tmp_path: Path) -> None:
    file_path = tmp_path / "viewport_default.json"
    _write_json(file_path, _base_payload())

    scenario = _load_scenarios(file_path)[0]

    assert scenario.viewport == ()


def test_load_scenarios_rejects_unknown_viewport(tmp_path: Path) -> None:
    file_path = tmp_path / "viewport_unknown.json"
    _write_json(file_path, _base_payload(viewport=["fhd", "8k"]))

    with pytest.raises(ValueError, match=r"viewport must be one of"):
        _load_scenarios(file_path)


@pytest.mark.parametrize("viewport", [123, {"name": "fhd"}, ["fhd", 1]])
def test_load_scenarios_rejects_invalid_viewport_types(tmp_path: Path, viewport: object) -> None:
    file_path = tmp_path / "viewport_invalid.json"
    _write_json(file_path, _base_payload(viewport=viewport))

    with pytest.raises(ValueError, match=r"viewport must be a string or list of strings"):
        _load_scenarios(file_path)
