from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QA_ROOT = ROOT / "qa"
OUTPUT_PATH = ROOT / "docs" / "MARKER_TESTS_MATRIX.md"

_IGNORE_MARKERS = {"parametrize", "scenario", "target", "order", "skip"}


def _marker_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _marker_name(node.func)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
        if isinstance(node.value.value, ast.Name) and node.value.value.id == "pytest" and node.value.attr == "mark":
            return node.attr
    return None


def _extract_module_markers(module: ast.Module) -> list[str]:
    markers: list[str] = []
    for stmt in module.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in stmt.targets):
            continue
        values = stmt.value.elts if isinstance(stmt.value, (ast.List, ast.Tuple, ast.Set)) else [stmt.value]
        for value in values:
            marker = _marker_name(value)
            if marker:
                markers.append(marker)
    return markers


def build_marker_to_tests_map() -> dict[str, list[str]]:
    marker_to_tests: dict[str, list[str]] = defaultdict(list)

    for path in sorted(QA_ROOT.rglob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            module = ast.parse(source)
        except SyntaxError:
            continue

        module_markers = set(_extract_module_markers(module))
        rel_path = path.relative_to(ROOT).as_posix()

        for node in module.body:
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue

            test_markers = set(module_markers)
            for decorator in node.decorator_list:
                marker = _marker_name(decorator)
                if marker:
                    test_markers.add(marker)

            test_id = f"{rel_path}::{node.name}"
            for marker in sorted(test_markers):
                if marker in _IGNORE_MARKERS:
                    continue
                marker_to_tests[marker].append(test_id)

    return {marker: sorted(tests) for marker, tests in sorted(marker_to_tests.items())}


def render_table(marker_to_tests: dict[str, list[str]]) -> str:
    lines: list[str] = []
    lines.append("# Marker -> Test Matrix")
    lines.append("")
    lines.append("Generowane automatycznie przez `tools/pytest/generate_marker_matrix.py`.")
    lines.append("Po zmianach markerow lub przypisania testow odswiez ten plik.")
    lines.append("")
    lines.append("| Marker | Lista testow |")
    lines.append("|---|---|")
    for marker, tests in marker_to_tests.items():
        joined = "<br>".join(f"`{test}`" for test in tests)
        lines.append(f"| `{marker}` | {joined} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    marker_to_tests = build_marker_to_tests_map()
    OUTPUT_PATH.write_text(render_table(marker_to_tests), encoding="utf-8")
    print(f"Wygenerowano: {OUTPUT_PATH}")
    print(f"Liczba markerow: {len(marker_to_tests)}")


if __name__ == "__main__":
    main()
