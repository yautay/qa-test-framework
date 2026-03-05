from __future__ import annotations

import os
from getpass import getpass
from time import time
from urllib.parse import urlsplit


def normalize_endpoint(raw_endpoint: str) -> str:
    endpoint = str(raw_endpoint).strip()
    if not endpoint:
        raise ValueError("missing endpoint")
    parsed = urlsplit(endpoint if "://" in endpoint else f"//{endpoint}")
    if parsed.path not in {"", "/"}:
        raise ValueError("endpoint path is not allowed; use host[:port] only")
    if parsed.query or parsed.fragment:
        raise ValueError("endpoint query/fragment is not allowed")
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        raise ValueError("endpoint scheme must be http or https")
    host_port = parsed.netloc.strip()
    if not host_port:
        raise ValueError("endpoint host is missing")
    if "@" in host_port:
        raise ValueError("credentials inside endpoint are not allowed")
    return host_port


def resolve_credentials(args, *, env_access_key: str, env_secret_key: str) -> tuple[str, str]:
    mode = str(getattr(args, "auth_mode", "env")).strip().lower()
    ask_flag = bool(getattr(args, "ask_release_credentials", False))
    if ask_flag:
        mode = "ask-release"

    if mode == "env":
        access_key = str(env_access_key).strip()
        secret_key = str(env_secret_key).strip()
        return access_key, secret_key

    if mode == "flags":
        access_key = str(getattr(args, "access_key", "") or "").strip()
        secret_key = str(getattr(args, "secret_key", "") or "").strip()
        return access_key, secret_key

    if mode != "ask-release":
        raise ValueError(f"unsupported auth mode: {mode}")

    access_key = str(getattr(args, "minio_access_key", "") or "").strip()
    if not access_key:
        access_key = str(getattr(args, "access_key", "") or "").strip()
    if not access_key:
        access_key = input("MinIO release access key: ").strip()
    if not access_key:
        raise ValueError("missing MinIO release access key")

    secret_key = getpass("MinIO release secret key: ").strip()
    if not secret_key:
        raise ValueError("missing MinIO release secret key")

    return access_key, secret_key


def build_release_destination_key(*, src_key: str, scratch_prefix: str) -> str:
    cleaned_prefix = str(scratch_prefix).strip().strip("/")
    if not cleaned_prefix:
        raise ValueError("scratch prefix cannot be empty")
    owner = os.getenv("USERNAME") or os.getenv("USER") or "unknown-user"
    run_id = str(int(time()))
    return f"{cleaned_prefix}/{owner}/{run_id}/{src_key.lstrip('/')}"


def is_access_denied_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "access denied" in text or "accessdenied" in text


def mask_secret(value: str, *, mask_ratio: float = 0.8) -> str:
    raw = str(value or "")
    if not raw:
        return "<empty>"

    length = len(raw)
    mask_count = max(1, int(round(length * mask_ratio)))
    if mask_count >= length:
        mask_count = length - 1

    visible = length - mask_count
    left_visible = (visible + 1) // 2
    right_visible = visible // 2
    masked_middle = "*" * mask_count
    right_part = raw[-right_visible:] if right_visible > 0 else ""
    return f"{raw[:left_visible]}{masked_middle}{right_part}"
