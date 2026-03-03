from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseline_ops import promote_candidates_local
from framework.env import load_env


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Promote local visual baselines from candidates to latest (repo + cache mirror)"
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Baseline profile (default: VISUAL_BASELINE_PROFILE)",
    )
    parser.add_argument(
        "--suite",
        action="append",
        default=[],
        help="Limit operation to selected suite (repeatable)",
    )
    parser.add_argument(
        "--prune-missing",
        action="store_true",
        help="Remove latest files that do not exist in candidates",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute writes. Without this flag command runs in dry-run mode",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    env = load_env()

    profile = str(args.profile or env.visual_baseline_profile).strip()
    suites = {str(item).strip() for item in args.suite if str(item).strip()} or None
    dry_run = not bool(args.apply)

    print("promote candidates -> latest")
    print(f"profile={profile}")
    print(f"suites={sorted(suites) if suites else 'ALL'}")
    print(f"mode={'dry-run' if dry_run else 'apply'}")

    promote_candidates_local(
        env,
        profile=profile,
        suites=suites,
        dry_run=dry_run,
        prune_missing=bool(args.prune_missing),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
