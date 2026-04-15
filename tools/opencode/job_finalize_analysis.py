from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize analysis handoff after user answers are provided.")
    parser.add_argument("--job-id", required=True, help="Job id under work/e2e-jobs/")
    parser.add_argument(
        "--answers-text",
        default="",
        help="Optional inline answers text captured during interactive chat.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow finalization even when answers look incomplete.",
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    job_dir = repo_root / "work" / "e2e-jobs" / str(args.job_id).strip()
    if not job_dir.is_dir():
        raise SystemExit(f"Job directory not found: {job_dir}")

    answers_path = job_dir / "analysis" / "answers.md"
    inline_answers = str(args.answers_text or "").strip()
    if inline_answers:
        answers_path.write_text(
            "\n".join(
                [
                    "# User Answers",
                    "",
                    inline_answers,
                    "",
                    f"_captured_at_utc: {_utc_now()}_",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    if not answers_path.exists():
        raise SystemExit(f"Answers file not found: {answers_path}")

    answers_text = answers_path.read_text(encoding="utf-8").strip()
    placeholder = "Add answers to open questions here."
    if not args.force:
        if len(answers_text) < 40 or placeholder in answers_text:
            raise SystemExit(
                "Answers look incomplete. Fill analysis/answers.md first, or use --force to finalize anyway."
            )

    handoff_path = job_dir / "handoff" / "analysis_contract.json"
    contract = _read_json(handoff_path)
    contract["status"] = "ready_for_implementation"
    contract["ready_for_implementation"] = True
    contract["updated_at_utc"] = _utc_now()
    contract["finalized_with_answers"] = str(answers_path.relative_to(job_dir))
    _write_json(handoff_path, contract)

    job_path = job_dir / "job.json"
    job = _read_json(job_path)
    job["status"] = "ready_for_implementation"
    job["updated_at_utc"] = _utc_now()
    _write_json(job_path, job)

    print(f"Analysis finalized for job: {job_dir.name}")
    print(f"Handoff status set to ready_for_implementation: {handoff_path}")
    print(f"Answers source: {answers_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
