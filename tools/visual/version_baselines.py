from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env
from framework.logger import configure_tools_logging
from tools.visual.version_baselines_commands import run_command
from tools.visual.version_baselines_parser import build_parser


def main() -> int:
    log_path = configure_tools_logging("version_baselines")
    logger.debug("tools_log_file", path=str(log_path), script="version_baselines")

    args = build_parser().parse_args()
    env = load_env()

    profile = str(args.profile or env.visual_baseline_profile).strip()
    suites = {str(item).strip() for item in args.suite if str(item).strip()} or None

    try:
        return run_command(args, env, profile=profile, suites=suites)
    except ValueError as exc:
        message = str(exc)
        print(f"error: {message}", file=sys.stderr)
        return 2 if "VISUAL_MINIO_ENDPOINT" in message else 1


if __name__ == "__main__":
    raise SystemExit(main())
