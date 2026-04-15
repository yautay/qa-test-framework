from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _copy_commands(*, source_dir: Path, target_dir: Path, overwrite: bool, dry_run: bool) -> tuple[int, int]:
    written = 0
    skipped = 0
    for source in sorted(source_dir.rglob("*.md")):
        relative_path = source.relative_to(source_dir)
        target = target_dir / relative_path
        if target.exists() and not overwrite:
            skipped += 1
            continue
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        written += 1
    return written, skipped


def _merge_agent_profiles(
    *,
    config_path: Path,
    profile_path: Path,
    overwrite: bool,
    dry_run: bool,
) -> tuple[int, int]:
    config = _load_json(config_path)
    profiles = _load_json(profile_path)

    profile_agents = profiles.get("agents")
    if not isinstance(profile_agents, dict):
        raise ValueError(f"Missing 'agents' object in {profile_path}")

    config_agents = config.setdefault("agents", {})
    if not isinstance(config_agents, dict):
        raise ValueError(f"Existing 'agents' value in {config_path} is not an object")

    merged = 0
    skipped = 0
    for name, agent_config in profile_agents.items():
        if not isinstance(agent_config, dict):
            raise ValueError(f"Agent profile '{name}' in {profile_path} is not an object")
        if name in config_agents and not overwrite:
            skipped += 1
            continue
        config_agents[name] = agent_config
        merged += 1

    if merged > 0 and not dry_run:
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    return merged, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Register OpenCode project commands from tools/opencode/commands into .opencode/commands. "
            "Optional: merge agent profiles into .opencode.json."
        )
    )
    parser.add_argument(
        "--overwrite-commands",
        action="store_true",
        help="Overwrite existing files in .opencode/commands.",
    )
    parser.add_argument(
        "--with-agent-profiles",
        action="store_true",
        help="Merge tools/opencode/opencode.agents.json into .opencode.json.",
    )
    parser.add_argument(
        "--overwrite-agent-profiles",
        action="store_true",
        help="Overwrite existing agent profiles when merging into .opencode.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be changed without writing files.",
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    source_commands_dir = repo_root / "tools" / "opencode" / "commands"
    target_commands_dir = repo_root / ".opencode" / "commands"
    target_config = repo_root / ".opencode.json"
    profile_path = repo_root / "tools" / "opencode" / "opencode.agents.json"

    if not source_commands_dir.is_dir():
        raise SystemExit(f"Source commands directory not found: {source_commands_dir}")

    written_commands, skipped_commands = _copy_commands(
        source_dir=source_commands_dir,
        target_dir=target_commands_dir,
        overwrite=bool(args.overwrite_commands),
        dry_run=bool(args.dry_run),
    )

    print(
        "Commands: "
        f"written={written_commands}, skipped={skipped_commands}, target='{target_commands_dir.relative_to(repo_root)}'"
    )

    if args.with_agent_profiles:
        merged, skipped = _merge_agent_profiles(
            config_path=target_config,
            profile_path=profile_path,
            overwrite=bool(args.overwrite_agent_profiles),
            dry_run=bool(args.dry_run),
        )
        print(f"Agent profiles: merged={merged}, skipped={skipped}, config='{target_config.relative_to(repo_root)}'")
        print("Note: agent profiles are stored in '.opencode.json' (repo root), not under '.opencode/'.")

    if args.dry_run:
        print("Dry run complete. No files were written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
