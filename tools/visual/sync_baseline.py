from __future__ import annotations

from pathlib import Path

from framework.env import load_env
from framework.visual.baseline_store import BaselineStore


def main() -> int:
    env = load_env()
    repo_root = Path(__file__).resolve().parents[2]
    store = BaselineStore(env, repo_root)
    cache_dir = repo_root / env.visual_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"Baseline cache directory ready: {cache_dir}")
    print("Use visual tests to lazy-download required baseline objects.")
    print(f"Provider: {env.visual_baseline_provider}")
    print(f"Profile: {env.visual_baseline_profile}")
    print(f"Version: {env.visual_baseline_version}")
    _ = store
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
