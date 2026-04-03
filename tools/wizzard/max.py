import os
import shutil
import subprocess
import sys

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from tools.wizzard.locators import INPUTS_vms_nc_ssh

nc_container_pass = "nc123"


def find_chrome_executable() -> str:
    if sys.platform.startswith("linux"):
        candidates = [
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
        ]
    elif sys.platform == "darwin":  # macOS
        candidates = [shutil.which("google-chrome"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    elif sys.platform == "win32":
        candidates = [
            shutil.which("chrome"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ]
    else:
        candidates = []

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    raise FileNotFoundError("Nie znaleziono przeglądarki Chrome/Chromium w systemie.")


WIZARD_AUTH = "Basic bmMtdGVjaC11c2VyOnlnQldYYzBObVNqS3ZnQlZlbkl4SHRoVg=="


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
    vms_ssh = page.locator(INPUTS_vms_nc_ssh)
    elements = vms_ssh.all()
    inputs_data = []
    for el in elements:
        input_id_attr = el.get_attribute("id") or ""
        input_id = input_id_attr.split("-")[0] if input_id_attr else ""
        input_value = el.input_value().split()
        host = input_value[1]
        port = input_value[-1]
        if "nodekom" in host:
            continue
        inputs_data.append({"id": input_id, "host": host, "port": port})

    print("VMS Report:")
    for i, data in enumerate(inputs_data, 1):
        print(f"{i}. id={data['id']}, host={data['host']}, port={data['port']}")

    browser.close()
    pw.stop()
    return inputs_data


def check_vm_crontab(ssh_host: str, ssh_port: str) -> bool:
    command = [
        "sshpass",
        "-p",
        nc_container_pass,
        "ssh -o StrictHostKeyChecking=no",
        "-p",
        ssh_port,
        ssh_host,
        r'crontab -l | grep -vE "^\s*(#|$)"',
    ]

    if os.name == "nt":  # Windows
        cmd = (
            f"sshpass -p {nc_container_pass} ssh -o StrictHostKeyChecking=no -p {ssh_port} {ssh_host} "
            r'crontab -l | grep -vE "^\s*(#|$)"'
        )
        command = ["wsl", "bash", "-c", cmd]

    try:
        result = subprocess.run(command, timeout=600, capture_output=True, text=True)

        output = result.stdout.strip()

        if not output:
            output = "Nothing"
            print("Crontab active:", output)
        else:
            print("Crontab active entries:\n", output)
        return result.returncode in {0, 1}

    except subprocess.TimeoutExpired:
        print("Command timed out.")
        return False


def check_vm_mock(ssh_host: str, ssh_port: str) -> bool:
    remote_cmd = (
        "grep -m1 \"'enabled'\" /srv/http/netcorner/config/config.d/mock.php "
        "| sed -E \"s/.*'enabled' => ([a-z]+).*/\\1/i\""
    )
    command = [
        "sshpass",
        "-p",
        nc_container_pass,
        "ssh -o StrictHostKeyChecking=no",
        "-p",
        ssh_port,
        ssh_host,
        remote_cmd,
    ]

    if os.name == "nt":  # Windows
        cmd = f"sshpass -p {nc_container_pass} ssh -o StrictHostKeyChecking=no -p {ssh_port} {ssh_host} {remote_cmd}"
        command = ["wsl", "bash", "-c", cmd]

    try:
        result = subprocess.run(command, timeout=600, capture_output=True, text=True)

        output = result.stdout.strip()
        print("Mock enabled:", output)
        return result.returncode in {0, 1}

    except subprocess.TimeoutExpired:
        print("Command timed out.")
        return False


if __name__ == "__main__":
    vms_wizard = parse_wizard()
    for vm in vms_wizard:
        print("-------------------{}-------------------".format(vm["id"]))
        check_vm_crontab(vm["host"], vm["port"])
        check_vm_mock(vm["host"], vm["port"])
