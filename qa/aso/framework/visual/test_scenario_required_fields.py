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
