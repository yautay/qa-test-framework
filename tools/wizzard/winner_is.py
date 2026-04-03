import shutil
import sys
from collections import Counter, defaultdict

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from tools.wizzard.locators import CONTAINERS_all, ELEMENTS_test_owners, ELEMENTS_test_vms

WIZARD_AUTH = "Basic bmMtdGVjaC11c2VyOnlnQldYYzBObVNqS3ZnQlZlbkl4SHRoVg=="


def find_chrome_executable() -> str:
    if sys.platform.startswith("linux"):
        candidates = [
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
        ]
    elif sys.platform == "darwin":
        candidates = [shutil.which("google-chrome"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    elif sys.platform == "win32":
        candidates = [
            shutil.which("chrome"),
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
    else:
        candidates = []

    for path in candidates:
        if path and (path.startswith("C:") or path.startswith("/")):
            from pathlib import Path

            if Path(path).exists():
                return path
    raise FileNotFoundError("Nie znaleziono Chrome/Chromium")


def get_rendered_page() -> tuple[Playwright, Browser, Page]:
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True, executable_path=find_chrome_executable(), args=["--no-sandbox", "--ignore-certificate-errors"]
    )

    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.set_extra_http_headers({"Authorization": WIZARD_AUTH})

    def handle_dialog(dialog):
        dialog.dismiss()

    page.on("dialog", handle_dialog)

    try:
        page.goto("https://test-wizard.netcorner.pl/", wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"Warning: Could not load page: {e}")
        print(f"Page URL: {page.url}")
        print(f"Page title: {page.title()}")

    return pw, browser, page


def parse_wizard() -> list:
    pw, browser, page = get_rendered_page()
    vms = page.locator(CONTAINERS_all + ELEMENTS_test_vms).all()
    vms_report = []
    for vm in vms:
        vm_id = vm.inner_text().strip()
        owner_locator = ELEMENTS_test_owners.format(vm=vm_id)
        owner = page.locator(owner_locator).inner_text().strip()
        vms_report.append({"id": vm_id, "owner": owner})
    browser.close()
    pw.stop()
    return vms_report


if __name__ == "__main__":
    vms_wizard = parse_wizard()
    counter = Counter(item["owner"] for item in vms_wizard)
    raport = counter.most_common()

    ranking = defaultdict(list)
    for owner, count in counter.items():
        ranking[count].append(owner)

    sorted_counts = sorted(ranking.keys(), reverse=True)

    medals = {0: "🥇 ZŁOTO", 1: "🥈 SREBRO", 2: "🥉 BRĄZ"}

    print("\n🧪📊 WIELKI RANKING POSIADACZY TESTÓWEK 2025 🎉")
    print("Kto rządzi testówkami? Kto zbiera je jak Pokemony? Sprawdźmy!\n")

    place = 0

    for _i, count in enumerate(sorted_counts):
        if place > 2:
            break

        owners = ", ".join(ranking[count])
        medal = medals.get(place, "🏅")

        print(f"{medal}  MIEJSCE {place + 1}")
        print(f"👥 {owners}")
        print(f"🔥 Liczba testówek: {count}")

        if place == 0:
            print("👑 Legendarny poziom ogarnięcia! Wygrywa toster do opiekania chomików\n")
        elif place == 1:
            print("🛡️ Rycerze wirtualnych maszyn!\n")
        elif place == 2:
            print("🔧 Klikają szybciej niż Selenium mruga!\n")

        place += 1

    for owner, ile in raport:
        print(f"{owner}: {ile}")
