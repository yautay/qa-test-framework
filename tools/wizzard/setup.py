"""Setup frontu i backendu testowki przez Wizard.

Uzycie:
  .venv/bin/python tools/wizzard/setup.py
  .venv/bin/python tools/wizzard/setup.py --host kocopoly.test
  .venv/bin/python tools/wizzard/setup.py --host kocopoly.test --skip-indexer
  .venv/bin/python tools/wizzard/setup.py --host kocopoly.test --index-only
  .venv/bin/python tools/wizzard/setup.py --help

Opcje:
  --host <nazwa.env>  Nadpisuje server_name z settings_cli.py.
  --front-branch <nazwa>   Branch dla frontu (domyslnie: develop).
  --backend-branch <nazwa> Branch dla backendu (domyslnie: develop).
  --skip-indexer           Pomija koncowa indeksacje Solr na backendzie.
  --index-only             Wykonuje tylko polaczenie backend + indeksacje Solr.
  --help, --hellp     Pokazuje pomoc.

Przebieg:
  1) Odczytuje host/port SSH frontu i backendu z test-wizard.netcorner.pl.
  2) Weryfikuje polaczenie SSH (echo ok).
  3) Front: ktr -> git checkout develop -> git pull -> ./scripts/bin/build.sh
  4) Backend: ktr -> git checkout develop -> git pull -> gulp deploy-local
     -> ./symfony crontab:cron:solr-product-indexer (chyba ze --skip-indexer)
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
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--skip-indexer",
        action="store_true",
        help="Pomija koncowa indeksacje Solr na backendzie",
    )
    mode_group.add_argument(
        "--index-only",
        action="store_true",
        help="Wykonuje tylko backendowy krok indeksacji Solr",
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


def run_ssh_stream(ssh_host: str, ssh_port: str, command: str, prefix: str, timeout_s: int = 60) -> int:
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

    process = subprocess.Popen(
        ssh_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        assert process.stdout is not None
        for line in process.stdout:
            print(f"[{prefix}] {line.rstrip()}", flush=True)
        return process.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        print(f"[{prefix}] TIMEOUT po {timeout_s}s", flush=True)
        return 124


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
        f"bash -ic 'ktr && git checkout {branch} && git pull "
        "&& rm -rf ~/.cache/node && ./scripts/bin/build.sh'"
    )
    print(f"[front] uruchamiam: {front_command}")
    returncode = run_ssh_stream(host, port, front_command, prefix="front", timeout_s=3600)
    if returncode != 0:
        raise RuntimeError(f"Front setup zakonczyl sie bledem (kod={returncode})")


def run_backend_setup(host: str, port: str, branch: str, run_indexer: bool = True) -> None:
    backend_command = f"bash -ic 'ktr && git checkout {branch} && git pull && gulp deploy-local"
    if run_indexer:
        backend_command += " && ./symfony crontab:cron:solr-product-indexer"
    backend_command += "'"
    print(f"[backend] uruchamiam: {backend_command}")
    returncode = run_ssh_stream(host, port, backend_command, prefix="backend", timeout_s=5400)
    if returncode != 0:
        raise RuntimeError(f"Backend setup zakonczyl sie bledem (kod={returncode})")


def run_backend_indexer(host: str, port: str) -> None:
    indexer_command = "bash -ic 'ktr && ./symfony crontab:cron:solr-product-indexer'"
    print(f"[backend] uruchamiam: {indexer_command}")
    returncode = run_ssh_stream(host, port, indexer_command, prefix="backend-indexer", timeout_s=3600)
    if returncode != 0:
        raise RuntimeError(f"Backend indeksacja zakonczona bledem (kod={returncode})")


def print_execution_plan(args: argparse.Namespace, server_name: str, vm_name: str) -> None:
    full_setup_mode = not args.index_only
    selected_front_branch = args.front_branch
    selected_backend_branch = args.backend_branch

    print("--- Plan wykonania ---")
    print(f"host/server_name: {server_name}")
    print(f"vm_name: {vm_name}")
    print(f"tryb: {'index-only' if args.index_only else 'full-setup'}")
    print(f"skip-indexer: {'tak' if args.skip_indexer else 'nie'}")
    print(f"front-branch: {selected_front_branch}")
    print(f"backend-branch: {selected_backend_branch}")

    if args.index_only:
        print("kroki: backend verify_connection -> backend indexer")
    else:
        backend_step = "backend setup (bez indexera)" if args.skip_indexer else "backend setup + indexer"
        print(f"kroki: backend verify_connection -> front verify_connection -> front setup -> {backend_step}")

    if full_setup_mode:
        print("uwaga: front/backend branch beda checkoutowane i pullowane podczas setupu")
    else:
        print("uwaga: w trybie index-only branche nie sa checkoutowane")
    print("----------------------")


if __name__ == "__main__":
    args = parse_args()
    resolved_server_name = args.server_name.strip() if args.server_name else load_server_name()
    resolved_vm_name = vm_name_from_server_name(resolved_server_name)
    print_execution_plan(args, resolved_server_name, resolved_vm_name)
    print(f"server_name={resolved_server_name}")
    print(f"vm_name={resolved_vm_name}")

    ssh_info = get_vm_ssh_info(resolved_vm_name)
    backend_host, backend_port = ssh_info["backend"]
    front_host, front_port = ssh_info["front"]

    print(f"backend ssh: nc@{backend_host}:{backend_port}")
    print(f"front ssh:   nc@{front_host}:{front_port}")

    print("[setup] Krok: weryfikacja polaczenia backend")
    verify_connection("backend", backend_host, backend_port)
    if args.index_only:
        print("[setup] Krok: uruchomienie indeksacji backend (index-only)")
        run_backend_indexer(backend_host, backend_port)
        print("Indeksacja zakonczona pomyslnie.")
        raise SystemExit(0)

    print("[setup] Krok: weryfikacja polaczenia front")
    verify_connection("front", front_host, front_port)
    print("[setup] Krok: setup front")
    run_front_setup(front_host, front_port, args.front_branch)
    print("[setup] Krok: setup backend")
    run_backend_setup(backend_host, backend_port, args.backend_branch, run_indexer=not args.skip_indexer)
    print("Setup zakonczony pomyslnie.")
