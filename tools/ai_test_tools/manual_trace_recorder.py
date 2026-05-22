#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright


@dataclass(slots=True)
class RecorderConfig:
    start_url: str
    scenario_name: str
    target_domain: str
    output_dir: Path
    browser: str
    slow_mo_ms: int
    resizable_window: bool


def parse_args() -> RecorderConfig:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Manual Playwright trace recorder for collecting user flow artifacts "
            "for new automated tests."
        ),
        epilog=(
            "Przyklady:\n"
            "  .venv/bin/python tools/ai_test_tools/manual_trace_recorder.py \\\n"
            "    --start-url \"https://example.test.netcorner.pl/\" \\\n"
            "    --scenario-name \"guest_checkout_happy_path\" \\\n"
            "    --target-domain \"nuxt\"\n\n"
            "  .venv/bin/python tools/ai_test_tools/manual_trace_recorder.py \\\n"
            "    --start-url \"https://admin-example.test.netcorner.pl/admin.php\" \\\n"
            "    --target-domain \"admin\" --fixed-viewport\n\n"
            "Komendy interaktywne podczas nagrania:\n"
            "  c  dodaj checkpoint (opcjonalny wskazany element + screenshot)\n"
            "  u  cofnij ostatni checkpoint\n"
            "  e  edytuj ostatni checkpoint\n"
            "  s  zapisz artefakty i zakoncz\n"
            "  h  pokaz pomoc\n"
            "  q  przerwij i zapisz to, co juz jest"
        ),
    )
    parser.add_argument("--start-url", required=True, help="Start URL for recording session.")
    parser.add_argument(
        "--scenario-name",
        default="manual_flow",
        help="Scenario label used in artifact metadata and directory naming.",
    )
    parser.add_argument(
        "--target-domain",
        default="unknown",
        help="Domain label (nuxt/admin/mailhog/setup/custom).",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/manual-traces",
        help="Base output directory for generated artifacts.",
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Playwright browser engine.",
    )
    parser.add_argument(
        "--slow-mo-ms",
        type=int,
        default=100,
        help="Delay between browser actions in milliseconds.",
    )
    parser.add_argument(
        "--fixed-viewport",
        action="store_true",
        help=(
            "Use Playwright default fixed viewport (1280x720). "
            "By default window is resizable and viewport follows window size."
        ),
    )

    args = parser.parse_args()
    return RecorderConfig(
        start_url=args.start_url,
        scenario_name=args.scenario_name.strip() or "manual_flow",
        target_domain=args.target_domain.strip() or "unknown",
        output_dir=Path(args.output_dir),
        browser=args.browser,
        slow_mo_ms=max(args.slow_mo_ms, 0),
        resizable_window=not args.fixed_viewport,
    )


def make_run_dir(base_dir: Path, scenario_name: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_name = "_".join(scenario_name.lower().split())
    run_dir = base_dir / f"{timestamp}_{safe_name}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def create_metadata(config: RecorderConfig) -> dict[str, str]:
    return {
        "scenario_name": config.scenario_name,
        "target_domain": config.target_domain,
        "start_url": config.start_url,
        "browser": config.browser,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "note": (
            "Base host is not fixed by design. Reuse path semantics and business intent "
            "across environments."
        ),
    }


def extract_path_hint(url: str) -> str:
    if "/" not in url:
        return "/"
    parts = url.split("/", 3)
    if len(parts) < 4:
        return "/"
    return "/" + parts[3]


def arm_element_picker(page: Page) -> None:
    page.evaluate(
        """
() => {
  window.__oc_pick = null;
  if (window.__oc_pick_handler) {
    document.removeEventListener('click', window.__oc_pick_handler, true);
  }

  const cssPath = (el) => {
    if (!(el instanceof Element)) return null;
    const segments = [];
    let current = el;
    while (current && current.nodeType === Node.ELEMENT_NODE && segments.length < 6) {
      let segment = current.tagName.toLowerCase();
      if (current.id) {
        segment += `#${CSS.escape(current.id)}`;
        segments.unshift(segment);
        break;
      }
      const cls = Array.from(current.classList || [])
        .slice(0, 2)
        .map((c) => `.${CSS.escape(c)}`)
        .join('');
      if (cls) segment += cls;
      const parent = current.parentElement;
      if (parent) {
        const sameTagSiblings = Array.from(parent.children).filter((n) => n.tagName === current.tagName);
        if (sameTagSiblings.length > 1) {
          const idx = sameTagSiblings.indexOf(current) + 1;
          segment += `:nth-of-type(${idx})`;
        }
      }
      segments.unshift(segment);
      current = current.parentElement;
    }
    return segments.join(' > ');
  };

  window.__oc_pick_handler = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const target = event.target;
    if (!(target instanceof Element)) return;

    const textRaw = (target.textContent || '').replace(/\s+/g, ' ').trim();
    const text = textRaw.slice(0, 180);
    const testId = target.getAttribute('data-testid') || target.getAttribute('data-test') || target.getAttribute('data-qa');
    const ariaLabel = target.getAttribute('aria-label');
    const role = target.getAttribute('role');
    const nameAttr = target.getAttribute('name');

    const selectorCandidates = [];
    if (testId) {
      selectorCandidates.push(`[data-testid="${CSS.escape(testId)}"]`);
      selectorCandidates.push(`[data-test="${CSS.escape(testId)}"]`);
      selectorCandidates.push(`[data-qa="${CSS.escape(testId)}"]`);
    }
    if (target.id) selectorCandidates.push(`#${CSS.escape(target.id)}`);
    if (ariaLabel) selectorCandidates.push(`${target.tagName.toLowerCase()}[aria-label="${CSS.escape(ariaLabel)}"]`);
    if (nameAttr) selectorCandidates.push(`${target.tagName.toLowerCase()}[name="${CSS.escape(nameAttr)}"]`);

    const css = cssPath(target);
    if (css) selectorCandidates.push(css);

    window.__oc_pick = {
      tag: target.tagName.toLowerCase(),
      id: target.id || null,
      text,
      role,
      aria_label: ariaLabel,
      name: nameAttr,
      test_id: testId,
      css_path: css,
      selector_candidates: Array.from(new Set(selectorCandidates)).slice(0, 8),
      picked_at: new Date().toISOString(),
    };

    document.removeEventListener('click', window.__oc_pick_handler, true);
  };

  document.addEventListener('click', window.__oc_pick_handler, true);
}
"""
    )


def get_picked_element(page: Page) -> dict[str, object] | None:
    picked = page.evaluate("() => window.__oc_pick || null")
    if isinstance(picked, dict):
        return picked
    return None


def pick_element_for_assertion(page: Page) -> dict[str, object] | None:
    arm_element_picker(page)
    print("Tryb wyboru aktywny. Kliknij jeden element w przegladarce i nacisnij Enter tutaj.")
    input()
    picked = get_picked_element(page)
    if not picked:
        print("Nie wybrano elementu. Checkpoint bedzie zapisany bez powiazania elementu.")
        return None
    print(
        "Wybrany element: "
        f"tag={picked.get('tag')} id={picked.get('id')} text={picked.get('text')!r}"
    )
    return picked


def capture_checkpoint(page: Page, screenshots_dir: Path, checkpoints: list[dict[str, object]]) -> None:
    bind_element = input("Powiazac checkpoint z konkretnym elementem? [y/N]: ").strip().lower() == "y"
    picked_element = pick_element_for_assertion(page) if bind_element else None

    print("Przyklad etykiety: cart_contains_added_product")
    label = input("Etykieta checkpointu: ").strip()
    if not label:
        print("Pominieto checkpoint: pusta etykieta.")
        return

    print("Przyklad oczekiwania: W koszyku widoczny 1 produkt i poprawna cena")
    expectation = input("Oczekiwanie (co ma byc asercja): ").strip()
    severity = input("Waznosc [critical|major|minor] (domyslnie=major): ").strip().lower() or "major"
    kind = input("Typ [ui|api|data] (domyslnie=ui): ").strip().lower() or "ui"
    print("Przyklad hintu: wybierz pierwszy produkt z badge 'Promocja' i cena < 200")
    automation_hint = input(
        "Hint automatyzacyjny (opcjonalny): "
    ).strip()
    selection_strategy = input(
        "Strategia wyboru [exact|dynamic] (domyslnie=exact): "
    ).strip().lower() or "exact"
    if selection_strategy not in {"exact", "dynamic"}:
        print("Nieznana strategia, ustawiam 'exact'.")
        selection_strategy = "exact"
    if selection_strategy == "dynamic" and not automation_hint:
        print("Strategia 'dynamic' wymaga hintu automatyzacyjnego. Checkpoint nie zapisany.")
        return

    shot_name = f"{len(checkpoints) + 1:03d}_{'_'.join(label.split())}.png"
    shot_path = screenshots_dir / shot_name
    page.screenshot(path=str(shot_path), full_page=True)

    checkpoint = {
        "name": label,
        "type": kind,
        "severity": severity,
        "expectation": expectation,
        "automation_hint": automation_hint,
        "selection_strategy": selection_strategy,
        "url": page.url,
        "path_hint": extract_path_hint(page.url),
        "title": page.title(),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "screenshot": f"screenshots/{shot_name}",
    }
    if picked_element:
        checkpoint["element"] = picked_element
    checkpoints.append(checkpoint)
    print(f"Checkpoint zapisany: {label}")


def undo_last_checkpoint(run_dir: Path, checkpoints: list[dict[str, object]]) -> None:
    if not checkpoints:
        print("Brak checkpointow do cofniecia.")
        return

    last = checkpoints.pop()
    screenshot_rel = last.get("screenshot")
    if isinstance(screenshot_rel, str):
        screenshot_path = run_dir / screenshot_rel
        if screenshot_path.exists():
            screenshot_path.unlink()
    print(f"Cofnieto checkpoint: {last.get('name', '<bez nazwy>')}")


def _edit_value(label: str, current: str) -> str:
    updated = input(f"{label} [{current}]: ").strip()
    return updated if updated else current


def edit_last_checkpoint(checkpoints: list[dict[str, object]]) -> None:
    if not checkpoints:
        print("Brak checkpointow do edycji.")
        return

    last = checkpoints[-1]
    print(f"Edycja checkpointu: {last.get('name', '<bez nazwy>')}")
    print("Wpisz nowa wartosc lub Enter, aby zostawic bez zmian.")

    last["name"] = _edit_value("Etykieta", str(last.get("name", "")))
    last["expectation"] = _edit_value("Oczekiwanie", str(last.get("expectation", "")))
    last["severity"] = _edit_value("Waznosc", str(last.get("severity", "major")))
    last["type"] = _edit_value("Typ", str(last.get("type", "ui")))
    last["selection_strategy"] = _edit_value(
        "Strategia [exact|dynamic]", str(last.get("selection_strategy", "exact"))
    )
    last["automation_hint"] = _edit_value(
        "Hint automatyzacyjny", str(last.get("automation_hint", ""))
    )

    if str(last.get("selection_strategy", "exact")).lower() == "dynamic" and not str(
        last.get("automation_hint", "")
    ).strip():
        print("Strategia 'dynamic' wymaga hintu automatyzacyjnego. Przywracam 'exact'.")
        last["selection_strategy"] = "exact"

    print(f"Zaktualizowano checkpoint: {last.get('name', '<bez nazwy>')}")


def write_json(path: Path, payload: object) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=True)
        file.write("\n")


def run_session(config: RecorderConfig) -> int:
    run_dir = make_run_dir(config.output_dir, config.scenario_name)
    screenshots_dir = run_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    trace_path = run_dir / "trace.zip"
    checkpoints_path = run_dir / "checkpoints.json"
    metadata_path = run_dir / "metadata.json"

    checkpoints: list[dict[str, object]] = []
    metadata = create_metadata(config)

    with sync_playwright() as p:
        browser_launcher = getattr(p, config.browser)
        browser = browser_launcher.launch(
            headless=False,
            slow_mo=config.slow_mo_ms,
            args=["--start-maximized"] if config.resizable_window else None,
        )
        context_kwargs = {"ignore_https_errors": True}
        if config.resizable_window:
            context_kwargs["no_viewport"] = True
        context: BrowserContext = browser.new_context(**context_kwargs)
        page = context.new_page()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

        print("\n--- Manual Trace Recorder ---")
        print(f"Scenario      : {config.scenario_name}")
        print(f"Target domain : {config.target_domain}")
        print(f"Start URL     : {config.start_url}")
        print(f"Run directory : {run_dir}")
        print("\nCommands:")
        print("  c = capture checkpoint")
        print("  u = undo last checkpoint")
        print("  e = edit last checkpoint")
        print("  s = save and stop recording")
        print("  h = show commands")
        print("  q = abort recording (save current artifacts)")

        page.goto(config.start_url)
        print("\nBrowser opened. Execute the user flow manually.")

        try:
            while True:
                cmd = input("\ncommand [c/u/e/s/h/q]: ").strip().lower()
                if cmd == "c":
                    capture_checkpoint(page, screenshots_dir, checkpoints)
                elif cmd == "u":
                    undo_last_checkpoint(run_dir, checkpoints)
                elif cmd == "e":
                    edit_last_checkpoint(checkpoints)
                elif cmd == "h":
                    print(
                        "Commands: c=checkpoint (supports element binding), "
                        "u=undo last checkpoint, e=edit last checkpoint, "
                        "s=save+stop, h=help, q=abort+save"
                    )
                elif cmd == "s":
                    break
                elif cmd == "q":
                    print("Abort requested. Saving current artifacts.")
                    break
                else:
                    print("Unknown command. Type h for help.")
        finally:
            context.tracing.stop(path=str(trace_path))
            context.close()
            browser.close()

    write_json(checkpoints_path, checkpoints)
    write_json(metadata_path, metadata)

    print("\nArtifacts created:")
    print(f"- Trace       : {trace_path}")
    print(f"- Checkpoints : {checkpoints_path}")
    print(f"- Metadata    : {metadata_path}")
    print(f"- Screenshots : {screenshots_dir}")
    return 0


def main() -> int:
    config = parse_args()
    return run_session(config)


if __name__ == "__main__":
    raise SystemExit(main())
