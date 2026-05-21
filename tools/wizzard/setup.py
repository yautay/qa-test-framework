"""Setup frontu i backendu testowki przez Wizard.

Uzycie:
  .venv/bin/python tools/wizzard/setup.py
  .venv/bin/python tools/wizzard/setup.py --host kocopoly.test
  .venv/bin/python tools/wizzard/setup.py --help

Opcje:
  --host <nazwa.env>  Nadpisuje server_name z settings_cli.py.
  --front-branch <nazwa>   Branch dla frontu (domyslnie: develop).
  --backend-branch <nazwa> Branch dla backendu (domyslnie: develop).
  --help, --hellp     Pokazuje pomoc.

Przebieg:
  1) Odczytuje host/port SSH frontu i backendu z test-wizard.netcorner.pl.
  2) Weryfikuje polaczenie SSH (echo ok).
  3) Front: ktr -> git checkout develop -> git pull -> ./scripts/bin/build.sh
  4) Backend: ktr -> git checkout develop -> git pull -> gulp deploy-local
     -> ./symfony crontab:cron:solr-product-indexer
"""

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

WIZARD_AUTH = "Basic bmMtdGVjaC11c2VyOnlnQldYYzBObVNqS3ZnQlZlbkl4SHRoVg=="
NC_CONTAINER_PASS = "nc123"
WIZARD_URL = "https://test-wizard.netcorner.pl/"


def find_chrome_executable() -> str:
    if sys.platform.startswith("linux"):
        candidates = [
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
        ]
    elif sys.platform == "darwin":
        candidates = [
            shutil.which("google-chrome"),
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
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
    raise FileNotFoundError("Nie znaleziono przegladarki Chrome/Chromium w systemie.")


def get_rendered_page() -> tuple[Playwright, Browser, Page]:
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        executable_path=find_chrome_executable(),
        args=["--no-sandbox", "--ignore-certificate-errors"],
    )
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.set_extra_http_headers({"Authorization": WIZARD_AUTH})
    page.goto(WIZARD_URL, wait_until="networkidle", timeout=30000)
    return pw, browser, page


def parse_ssh_value(raw_value: str) -> tuple[str, str] | None:
    value = raw_value.strip()
    if not value:
        return None

    match = re.search(r"ssh\s+[^@\s]+@(?P<host>[^\s]+)\s+-p\s+(?P<port>\d+)", value)
    if match:
        return match.group("host"), match.group("port")

    host_port_match = re.search(r"(?P<host>[^\s:]+):(?P<port>\d+)", value)
    if host_port_match:
        return host_port_match.group("host"), host_port_match.group("port")

    return None


def load_server_name() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    settings_path = repo_root / "settings_cli.py"
    spec = importlib.util.spec_from_file_location("settings_cli", settings_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Nie mozna zaladowac settings_cli.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server_name = getattr(module, "server_name", "").strip()
    if not server_name:
        raise ValueError("Brak server_name w settings_cli.py")
    return server_name


def vm_name_from_server_name(server_name: str) -> str:
    vm_name = server_name.split(".", 1)[0].strip()
    if not vm_name:
        raise ValueError(f"Nieprawidlowy server_name: {server_name!r}")
    return vm_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Setup front/backend dla testowki z wizarda")
    parser.add_argument(
        "--host",
        dest="server_name",
        help="Nazwa testowki, np. kocopoly.test. Nadpisuje server_name z settings_cli.py",
    )
    parser.add_argument(
        "--front-branch",
        default="develop",
        help="Branch dla frontu (domyslnie: develop)",
    )
    parser.add_argument(
        "--backend-branch",
        default="develop",
        help="Branch dla backendu (domyslnie: develop)",
    )
    parser.add_argument(
        "--hellp",
        action="help",
        help="Alias literowki dla --help",
    )
    return parser.parse_args()


def get_vm_ssh_info(vm_name: str) -> dict[str, tuple[str, str]]:
    backend_id = f"{vm_name}-test{vm_name}-backend-1-connection"
    front_id = f"{vm_name}-test{vm_name}-front-1-connection"

    pw, browser, page = get_rendered_page()
    try:
        backend_value = page.locator(f"#{backend_id}").input_value()
        front_value = page.locator(f"#{front_id}").input_value()
    finally:
        browser.close()
        pw.stop()

    backend = parse_ssh_value(backend_value)
    front = parse_ssh_value(front_value)

    if not backend:
        raise ValueError(f"Nie udalo sie sparsowac backend SSH dla {backend_id}")
    if not front:
        raise ValueError(f"Nie udalo sie sparsowac front SSH dla {front_id}")

    return {"backend": backend, "front": front}


def run_ssh(ssh_host: str, ssh_port: str, command: str, timeout_s: int = 60) -> subprocess.CompletedProcess[str]:
    ssh_command: list[str] = [
        "sshpass",
        "-p",
        NC_CONTAINER_PASS,
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "GlobalKnownHostsFile=/dev/null",
        "-p",
        ssh_port,
        f"nc@{ssh_host}",
        command,
    ]

    if os.name == "nt":
        cmd = " ".join(ssh_command)
        ssh_command = ["wsl", "bash", "-lc", cmd]

    return subprocess.run(ssh_command, timeout=timeout_s, capture_output=True, text=True)


def verify_connection(name: str, host: str, port: str) -> None:
    result = run_ssh(host, port, "echo ok")
    output = result.stdout.strip()
    if result.returncode == 0 and output == "ok":
        print(f"[{name}] polaczenie OK: nc@{host}:{port}")
        return
    print(f"[{name}] polaczenie NIEUDANE: nc@{host}:{port}")
    if result.stderr.strip():
        print(result.stderr.strip())


def run_front_setup(host: str, port: str, branch: str) -> None:
    front_command = (
        f"bash -lc 'ktr && git checkout {branch} && git pull "
        "&& rm -rf ~/.cache/node && ./scripts/bin/build.sh'"
    )
    print(f"[front] uruchamiam: {front_command}")
    result = run_ssh(host, port, front_command, timeout_s=3600)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(f"Front setup zakonczyl sie bledem (kod={result.returncode})")


def run_backend_setup(host: str, port: str, branch: str) -> None:
    backend_command = (
        f"bash -lc 'ktr && git checkout {branch} && git pull && gulp deploy-local "
        "&& ./symfony crontab:cron:solr-product-indexer'"
    )
    print(f"[backend] uruchamiam: {backend_command}")
    result = run_ssh(host, port, backend_command, timeout_s=5400)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(f"Backend setup zakonczyl sie bledem (kod={result.returncode})")


if __name__ == "__main__":
    args = parse_args()
    resolved_server_name = args.server_name.strip() if args.server_name else load_server_name()
    resolved_vm_name = vm_name_from_server_name(resolved_server_name)
    print(f"server_name={resolved_server_name}")
    print(f"vm_name={resolved_vm_name}")

    ssh_info = get_vm_ssh_info(resolved_vm_name)
    backend_host, backend_port = ssh_info["backend"]
    front_host, front_port = ssh_info["front"]

    print(f"backend ssh: nc@{backend_host}:{backend_port}")
    print(f"front ssh:   nc@{front_host}:{front_port}")

    verify_connection("backend", backend_host, backend_port)
    verify_connection("front", front_host, front_port)
    run_front_setup(front_host, front_port, args.front_branch)
    run_backend_setup(backend_host, backend_port, args.backend_branch)
    print("Setup zakonczony pomyslnie.")
