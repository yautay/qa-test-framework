from __future__ import annotations

import re
from pathlib import Path

SECTION_LINE = "=" * 50


def main() -> int:
    mf = Path(__file__).resolve().parents[2] / "Makefile"

    print()
    print("Usage:")
    print("  make <target>")
    print()

    rx_target = re.compile(r"^([A-Za-z0-9_.-]+):.*?##\s*(.+)$")
    rx_section = re.compile(r"^##@(.+)$")

    current_section = None

    for line in mf.read_text(encoding="utf-8").splitlines():
        sec = rx_section.match(line)
        if sec:
            current_section = sec.group(1).strip()
            print()
            print(SECTION_LINE)
            print(current_section.upper())
            print(SECTION_LINE)
            continue

        m = rx_target.match(line)
        if m:
            target, desc = m.groups()
            print(f"  {target:<22} {desc}")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
