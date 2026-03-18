from __future__ import annotations

from pathlib import Path

from loguru import logger

try:
    import pyperclip

    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

from framework.logger import configure_tools_logging
from framework.visual.scenario_loader import load_scenarios_with_errors


def generate_visual_tree() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    base_path = repo_root / "qa/visual/netcorner/nuxt/pl"

    categories = ["listings", "product_page", "hero_page", "layers"]

    tree_lines = ["qa/visual/netcorner/nuxt/pl/"]

    for category in categories:
        category_path = base_path / category
        tree_lines.append(f"├── {category}/")

        json_files: dict[str, list[str]] = {}

        for json_file in sorted(category_path.glob("*.json")):
            filename = json_file.name
            scenarios, _ = load_scenarios_with_errors(json_file.parent)
            urls = [s.target_url for s in scenarios if s.source_file.endswith(filename)]
            if urls:
                json_files[filename] = sorted(set(urls))

        files = sorted(json_files.keys())
        for i, filename in enumerate(files):
            is_last_file = i == len(files) - 1
            prefix = "└── " if is_last_file else "├── "
            tree_lines.append(f"{prefix}{filename}")

            urls = json_files[filename]
            for j, url in enumerate(urls):
                is_last_url = j == len(urls) - 1
                file_prefix = "    " if is_last_file else "│   "
                url_prefix = "└── " if is_last_url else "├── "
                tree_lines.append(f"{file_prefix}{url_prefix}{url}")

    return "\n".join(tree_lines)


def main() -> int:
    log_path = configure_tools_logging("generate_tree")
    logger.debug("tools_log_file", path=str(log_path), script="generate_tree")

    tree = generate_visual_tree()
    print(tree)

    if HAS_PYPERCLIP:
        pyperclip.copy(tree)  # type: ignore[has-type]
        print("\n✓ Copied to clipboard")
    else:
        print("\n✗ pyperclip not installed - skipping clipboard")

    repo_root = Path(__file__).resolve().parents[2]
    output_path = repo_root / "tools/artifacts/visual/visual_regression_tree.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(tree, encoding="utf-8")
    print(f"✓ Saved to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
