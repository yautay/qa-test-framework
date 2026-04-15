from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.opencode.cache_dom_snapshot import capture_dom_snapshot


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _normalize_paths(values: list[str], *, fallback: list[str], max_pages: int) -> list[str]:
    merged: list[str] = []
    for value in values + fallback:
        token = str(value or "").strip()
        if not token:
            continue
        if token not in merged:
            merged.append(token)
    if not merged:
        merged = ["/"]
    return merged[:max_pages]


def _render_journey_map(entries: list[dict[str, Any]]) -> str:
    lines: list[str] = ["# Journey Map", ""]
    for idx, item in enumerate(entries, start=1):
        lines.append(f"## Step {idx}")
        lines.append(f"- path: `{item['path']}`")
        lines.append(f"- final_url: `{item['final_url']}`")
        lines.append(f"- title: `{item['title']}`")
        h1_values = item.get("h1", [])
        if h1_values:
            lines.append("- h1:")
            for h1_item in h1_values[:3]:
                lines.append(f"  - {h1_item}")
        lines.append(f"- data-name count: {item['data_name_count']}")
        lines.append(f"- button count: {item['button_count']}")
        lines.append(f"- input count: {item['input_count']}")
        lines.append(f"- cache: `{item['latest_dir']}`")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _derive_locator_gaps(entries: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for item in entries:
        path = item["path"]
        summary = item.get("summary", {})
        data_name_count = int(item.get("data_name_count", 0))
        button_count = int(item.get("button_count", 0))
        input_count = int(item.get("input_count", 0))

        if data_name_count < 6 and (button_count + input_count) >= 6:
            findings.append(
                f"[{path}] Low stable attributes density: only {data_name_count} data-name elements for {button_count} buttons and {input_count} inputs."
            )

        for button in (summary.get("buttons") if isinstance(summary.get("buttons"), list) else [])[:40]:
            if not isinstance(button, dict):
                continue
            has_stable = bool(str(button.get("name") or "").strip() or str(button.get("id") or "").strip())
            if has_stable:
                continue
            label = str(button.get("text") or "").strip() or "<empty>"
            findings.append(f"[{path}] Button without stable selector: text={label!r}")

        for field in (summary.get("inputs") if isinstance(summary.get("inputs"), list) else [])[:40]:
            if not isinstance(field, dict):
                continue
            has_stable = bool(str(field.get("name") or "").strip() or str(field.get("id") or "").strip())
            if has_stable:
                continue
            field_type = str(field.get("type") or "").strip() or "unknown"
            findings.append(f"[{path}] Input without stable selector: type={field_type!r}")
    deduped: list[str] = []
    for row in findings:
        if row not in deduped:
            deduped.append(row)
    return deduped


def _render_locator_gaps(gaps: list[str]) -> str:
    lines = ["# Locator Gaps", "", "## Summary"]
    if not gaps:
        lines.append("- No critical selector gaps detected in sampled pages.")
        return "\n".join(lines).strip() + "\n"
    lines.append(f"- Detected {len(gaps)} potential locator gaps.")
    lines.append("")
    lines.append("## Findings")
    for gap in gaps:
        lines.append(f"- {gap}")
    lines.append("")
    lines.append("## Product-side suggestions")
    lines.append("- Add `data-name` for high-value actions and form fields used by E2E flows.")
    lines.append("- Keep selector naming stable across releases.")
    return "\n".join(lines).strip() + "\n"


def _render_open_questions(entries: list[dict[str, Any]], gaps: list[str]) -> str:
    lines = ["# Open Questions", ""]
    lines.append("Please answer the following before implementation:")
    lines.append("")
    lines.append("- [ ] What is the expected success condition and final page/state for this scenario?")
    lines.append("- [ ] Which authentication mode should be used (guest/login/new registration)?")
    lines.append("- [ ] Which locale/currency rules are required for assertions?")
    lines.append("- [ ] Which delivery and payment variants are in scope and mandatory?")
    lines.append("- [ ] Should the test assert intermediate UI states or only business-critical outcomes?")
    if gaps:
        lines.append("- [ ] Can product add stable `data-name` attributes for listed locator gaps?")
    if len(entries) > 1:
        lines.append("- [ ] Confirm that all discovered paths are in scope for this job.")
    return "\n".join(lines).strip() + "\n"


def _render_refined_contract(entries: list[dict[str, Any]], gaps: list[str]) -> str:
    lines = ["# Refined Behavior Contract", "", "Status: DRAFT (needs user answers)", ""]
    lines.append("## Discovered pages")
    for item in entries:
        lines.append(f"- `{item['path']}` -> `{item['final_url']}` ({item['title']})")
    lines.append("")
    lines.append("## Current assumptions")
    lines.append("- Scenario execution will use runtime URL resolution via `--server-name`.")
    lines.append("- Test implementation will follow `page.section.component.method`.")
    lines.append("- Public PO methods will use `@step(...)`.")
    lines.append("- Existing wrappers will be reused before new wrapper creation.")
    lines.append("")
    lines.append("## Pending clarifications")
    lines.append("- See `analysis/open_questions.md` and fill `analysis/answers.md`.")
    if gaps:
        lines.append("- See `analysis/locator_gaps.md` for product-side selector improvements.")
    return "\n".join(lines).strip() + "\n"


def _write_job_status(job_path: Path, *, status: str) -> None:
    job = _read_json(job_path)
    job["status"] = status
    job["updated_at_utc"] = _utc_now()
    _write_json(job_path, job)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exploratory analysis pass for a versioned E2E job.")
    parser.add_argument("--job-id", required=True, help="Job id under work/e2e-jobs/")
    parser.add_argument("--path", action="append", default=[], help="Path to explore, repeatable")
    parser.add_argument("--paths-csv", default="", help="Comma-separated list of extra paths to explore")
    parser.add_argument("--max-pages", type=int, default=8, help="Maximum paths to analyze")
    parser.add_argument("--timeout-ms", type=int, default=45_000)
    parser.add_argument("--wait-after-load-ms", type=int, default=1_200)
    args = parser.parse_args()

    repo_root = _repo_root()
    job_dir = repo_root / "work" / "e2e-jobs" / str(args.job_id).strip()
    if not job_dir.is_dir():
        raise SystemExit(f"Job directory not found: {job_dir}")

    job_json_path = job_dir / "job.json"
    job = _read_json(job_json_path)
    target = job.get("target") if isinstance(job.get("target"), dict) else {}
    target_id = str(target.get("target_id") or "netcorner-nuxt-pl")
    server_name = str(target.get("server_name") or "").strip()
    if not server_name:
        raise SystemExit(f"Missing target.server_name in {job_json_path}")

    seed_paths = [
        str(item).strip() for item in (job.get("seed_paths") if isinstance(job.get("seed_paths"), list) else [])
    ]
    csv_paths = [item.strip() for item in str(args.paths_csv or "").split(",") if item.strip()]
    paths = _normalize_paths([*args.path, *csv_paths], fallback=seed_paths, max_pages=max(1, int(args.max_pages)))

    cache_root = job_dir / "analysis" / "cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for path in paths:
        captured = capture_dom_snapshot(
            server_name=server_name,
            page_path=path,
            target_id=target_id,
            output_root=cache_root,
            timeout_ms=int(args.timeout_ms),
            wait_after_load_ms=int(args.wait_after_load_ms),
        )
        summary = captured.get("summary") if isinstance(captured.get("summary"), dict) else {}
        item = {
            "path": str(path),
            "final_url": str(summary.get("url") or ""),
            "title": str(summary.get("title") or ""),
            "h1": summary.get("h1") if isinstance(summary.get("h1"), list) else [],
            "data_name_count": len(summary.get("data_name", [])) if isinstance(summary.get("data_name"), list) else 0,
            "button_count": len(summary.get("buttons", [])) if isinstance(summary.get("buttons"), list) else 0,
            "input_count": len(summary.get("inputs", [])) if isinstance(summary.get("inputs"), list) else 0,
            "latest_dir": str(captured.get("latest_dir") or ""),
            "summary_path": str(captured.get("summary_path") or ""),
            "summary": summary,
        }
        entries.append(item)

    analysis_dir = job_dir / "analysis"
    inventory_path = analysis_dir / "dom_inventory.json"
    _write_json(
        inventory_path,
        {
            "job_id": job.get("job_id"),
            "server_name": server_name,
            "target_id": target_id,
            "generated_at_utc": _utc_now(),
            "entries": entries,
        },
    )

    gaps = _derive_locator_gaps(entries)

    (analysis_dir / "journey_map.md").write_text(_render_journey_map(entries), encoding="utf-8")
    (analysis_dir / "locator_gaps.md").write_text(_render_locator_gaps(gaps), encoding="utf-8")
    (analysis_dir / "open_questions.md").write_text(_render_open_questions(entries, gaps), encoding="utf-8")
    (analysis_dir / "refined_behavior_contract.md").write_text(
        _render_refined_contract(entries, gaps), encoding="utf-8"
    )

    handoff_path = job_dir / "handoff" / "analysis_contract.json"
    _write_json(
        handoff_path,
        {
            "job_id": job.get("job_id"),
            "status": "needs_user_answers",
            "ready_for_implementation": False,
            "updated_at_utc": _utc_now(),
            "analysis_outputs": {
                "dom_inventory": str(inventory_path.relative_to(job_dir)),
                "journey_map": "analysis/journey_map.md",
                "locator_gaps": "analysis/locator_gaps.md",
                "open_questions": "analysis/open_questions.md",
                "answers": "analysis/answers.md",
                "refined_behavior_contract": "analysis/refined_behavior_contract.md",
            },
            "cached_paths": paths,
        },
    )

    _write_job_status(job_json_path, status="analysis_needs_answers")

    print(f"Analysis completed for job: {job_dir.name}")
    print(f"Journey map: {analysis_dir / 'journey_map.md'}")
    print(f"Locator gaps: {analysis_dir / 'locator_gaps.md'}")
    print(f"Open questions: {analysis_dir / 'open_questions.md'}")
    print(f"Handoff: {handoff_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
