from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "REPO_TREE.html"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".opencode",
    "artifacts",
    "build",
}


@dataclass(frozen=True)
class Node:
    path: Path
    is_dir: bool
    children: tuple["Node", ...] = ()


def build_tree(path: Path) -> Node:
    if not path.is_dir():
        return Node(path=path, is_dir=False)

    children: list[Node] = []
    for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if child.name in EXCLUDED_DIRS:
            continue
        children.append(build_tree(child))
    return Node(path=path, is_dir=True, children=tuple(children))


def render_node(node: Node, root: Path) -> str:
    rel = "." if node.path == root else node.path.relative_to(root).as_posix()
    label = escape(node.path.name if node.path != root else root.name)
    title = escape(rel)

    if not node.is_dir:
        return f'<li class="file" title="{title}">{label}</li>'

    if not node.children:
        return f'<li class="dir empty" title="{title}">{label}/</li>'

    child_html = "\n".join(render_node(child, root) for child in node.children)
    return (
        f"<li class=\"dir\" title=\"{title}\">"
        f"<details open><summary>{label}/</summary><ul>{child_html}</ul></details></li>"
    )


def render_html(tree: Node) -> str:
    items = render_node(tree, ROOT)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Repository Tree</title>
  <style>
    body {{ font-family: Menlo, Consolas, Monaco, monospace; margin: 24px; color: #1f2937; }}
    h1 {{ margin: 0 0 8px; font-size: 20px; }}
    p {{ margin: 0 0 16px; color: #4b5563; }}
    ul {{ list-style: none; margin: 0; padding-left: 18px; }}
    li {{ margin: 2px 0; }}
    .file::before {{ content: \"- \"; color: #9ca3af; }}
    .dir > details > summary {{ cursor: pointer; }}
    .empty::before {{ content: \"- \"; color: #9ca3af; }}
  </style>
</head>
<body>
  <h1>Repository Tree</h1>
  <p>Generated from project root. Excludes: {escape(', '.join(sorted(EXCLUDED_DIRS)))}</p>
  <ul>{items}</ul>
</body>
</html>
"""


def main() -> None:
    tree = build_tree(ROOT)
    OUTPUT.write_text(render_html(tree), encoding="utf-8")
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
