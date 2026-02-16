from __future__ import annotations

import json
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
VISUAL_ROOT = REPO_ROOT / "qa" / "visual"
RULES_FILE = VISUAL_ROOT / "validation_rules.json"


def _load_rules() -> list[dict]:
    payload = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("validation_rules.json: 'rules' must be a list")
    return [rule for rule in rules if isinstance(rule, dict)]


def _iter_scenario_files() -> list[Path]:
    files: list[Path] = []
    for path in VISUAL_ROOT.rglob("*.json"):
        if path.name == "validation_rules.json":
            continue
        files.append(path)
    return sorted(files)


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _match_rule(path: Path, rules: list[dict]) -> dict | None:
    rel = _relative(path)
    for rule in rules:
        path_regex = str(rule.get("path_regex", "")).strip()
        if path_regex and re.match(path_regex, rel):
            return rule
    return None


def _capture_first(regex: str, value: str) -> str | None:
    match = re.match(regex, value)
    if not match:
        return None
    if match.lastindex and match.lastindex >= 1:
        return match.group(1)
    return None


def _validate_file(path: Path, rules: list[dict], seen_ids: dict[str, str]) -> list[str]:
    rel = _relative(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []

    scenario_id = str(payload.get("id", "")).strip()
    target_url = str(payload.get("target_url", "")).strip()

    if not scenario_id:
        errors.append(f"{rel}: missing scenario id")
        return errors

    expected_name = f"{scenario_id}.json"
    if path.name != expected_name:
        errors.append(f"{rel}: file name must equal scenario id ({expected_name})")

    if scenario_id in seen_ids:
        errors.append(f"{rel}: duplicate scenario id, already used in {seen_ids[scenario_id]}")
    else:
        seen_ids[scenario_id] = rel

    rule = _match_rule(path, rules)
    if rule is None:
        errors.append(f"{rel}: no validation rule matched this path")
        return errors

    id_regex = str(rule.get("scenario_id_regex", "")).strip()
    url_regex = str(rule.get("target_url_regex", "")).strip()
    if id_regex and not re.match(id_regex, scenario_id):
        errors.append(f"{rel}: scenario id does not match regex: {id_regex}")
    if url_regex and not re.match(url_regex, target_url):
        errors.append(f"{rel}: target_url does not match regex: {url_regex}")

    if bool(rule.get("match_first_capture_group", False)):
        id_group = _capture_first(id_regex, scenario_id) if id_regex else None
        url_group = _capture_first(url_regex, target_url) if url_regex else None
        if id_group is None or url_group is None:
            errors.append(f"{rel}: capture-group comparison requested but missing captures")
        elif id_group != url_group:
            errors.append(
                f"{rel}: captured id mismatch scenario_id={id_group} target_url={url_group}"
            )

    return errors


def main() -> int:
    if not RULES_FILE.is_file():
        print(f"Visual validation rules not found: {RULES_FILE}")
        return 1

    rules = _load_rules()
    files = _iter_scenario_files()
    if not files:
        print("No visual scenario files found.")
        return 0

    all_errors: list[str] = []
    seen_ids: dict[str, str] = {}
    for file_path in files:
        all_errors.extend(_validate_file(file_path, rules, seen_ids))

    if all_errors:
        print("Visual scenario validation failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print(f"Visual scenario validation passed ({len(files)} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
